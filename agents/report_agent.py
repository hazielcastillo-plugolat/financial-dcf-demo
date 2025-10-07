"""Agent persisting scenario outputs to disk."""

from __future__ import annotations

from typing import cast

import pandas as pd

from core.models import Results, ScenarioResult, SensitivityPoint, Settings


class ReportAgent:
    """Save scenario summaries, FCFF tables, and collate artifact paths."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.resolve_paths()

    def save(
        self,
        scenarios: list[ScenarioResult],
        sensitivity: list[SensitivityPoint],
        data_preview: pd.DataFrame | None = None,
    ) -> dict[str, str]:
        """Persist CSV outputs and return artifact paths."""

        artifact_paths: dict[str, str] = {}

        summary_df = pd.DataFrame(
            [
                {
                    "scenario": scenario.name,
                    "wacc": scenario.wacc,
                    "npv": scenario.npv,
                    "irr": scenario.irr if scenario.irr is not None else "",
                }
                for scenario in scenarios
            ]
        )
        summary_path = self.settings.output_dir / "scenario_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        artifact_paths["scenario_summary"] = str(summary_path)

        for scenario in scenarios:
            fcff_df = pd.DataFrame(
                {
                    "year": list(range(1, len(scenario.fcff) + 1)),
                    "revenue": scenario.revenues,
                    "fcff": scenario.fcff,
                }
            )
            fcff_path = self.settings.output_dir / f"fcff_{scenario.name.lower()}.csv"
            fcff_df.to_csv(fcff_path, index=False)
            artifact_paths[f"fcff_{scenario.name.lower()}"] = str(fcff_path)

        if sensitivity:
            sensitivity_df = pd.DataFrame([point.dict() for point in sensitivity])
            sensitivity_csv = self.settings.output_dir / "sensitivity_overview.csv"
            sensitivity_df.to_csv(sensitivity_csv, index=False)
            artifact_paths["sensitivity_overview"] = str(sensitivity_csv)

        if data_preview is not None:
            data_path = self.settings.output_dir / "historical_data_preview.csv"
            data_preview.to_csv(data_path, index=False)
            artifact_paths["historical_data_preview"] = str(data_path)

        return artifact_paths

    @staticmethod
    def to_results(
        scenarios: list[ScenarioResult],
        sensitivity: list[SensitivityPoint],
        artifacts: dict[str, str],
        data_preview: pd.DataFrame | None,
    ) -> Results:
        """Assemble the pipeline results payload."""

        fcff_table: list[dict[str, float | int]] = []
        for index in range(len(scenarios[0].fcff)):
            row: dict[str, float | int] = {"year": index + 1}
            for scenario in scenarios:
                row[f"{scenario.name}_fcff"] = scenario.fcff[index]
            fcff_table.append(row)

        preview_records: list[dict[str, float | int]] = []
        if data_preview is not None:
            preview_records = cast(
                list[dict[str, float | int]],
                data_preview[["year", "revenue"]].to_dict(orient="records"),
            )

        return Results(
            scenarios=scenarios,
            sensitivity=sensitivity,
            fcff_table=fcff_table,
            artifacts=artifacts,
            data_preview=preview_records,
        )
