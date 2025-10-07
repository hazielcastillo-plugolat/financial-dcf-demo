"""Pipeline planner orchestrating the agent sequence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.models import Assumptions, Results, Settings
from core.scenarios import build_scenarios

from .assumption_agent import AssumptionAgent
from .data_agent import DataAgent
from .projection_agent import ProjectionAgent
from .report_agent import ReportAgent
from .sensitivity_agent import SensitivityAgent


class Planner:
    """Coordinates the data, validation, projection, and reporting agents."""

    def __init__(
        self,
        settings: Settings,
        data_agent: DataAgent | None = None,
        assumption_agent: AssumptionAgent | None = None,
        projection_agent: ProjectionAgent | None = None,
        sensitivity_agent: SensitivityAgent | None = None,
        report_agent: ReportAgent | None = None,
    ) -> None:
        self.settings = settings
        self.data_agent = data_agent or DataAgent(settings)
        self.assumption_agent = assumption_agent or AssumptionAgent()
        self.projection_agent = projection_agent or ProjectionAgent()
        self.sensitivity_agent = sensitivity_agent or SensitivityAgent(settings)
        self.report_agent = report_agent or ReportAgent(settings)

    def run_pipeline(
        self,
        assumptions: Assumptions,
        csv_path: Path | None = None,
        historical_df: pd.DataFrame | None = None,
    ) -> Results:
        """Execute the full pipeline and return the structured results."""

        data = self._resolve_data(assumptions, csv_path, historical_df)
        validated_assumptions = self.assumption_agent.validate(assumptions, data)
        scenarios = build_scenarios(validated_assumptions)
        scenario_results = self.projection_agent.run(validated_assumptions, scenarios)
        sensitivity_points, sensitivity_artifacts = self.sensitivity_agent.run(
            validated_assumptions, scenarios[0]
        )
        report_artifacts = self.report_agent.save(
            scenario_results, sensitivity_points, data
        )
        artifacts = {**report_artifacts, **sensitivity_artifacts}
        return ReportAgent.to_results(
            scenario_results, sensitivity_points, artifacts, data
        )

    def _resolve_data(
        self,
        assumptions: Assumptions,
        csv_path: Path | None,
        historical_df: pd.DataFrame | None,
    ) -> pd.DataFrame:
        if historical_df is not None:
            return historical_df
        if csv_path is not None:
            return self.data_agent.load_csv(csv_path)
        return self.data_agent.generate_synthetic(assumptions)
