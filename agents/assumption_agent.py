"""Agent responsible for validating assumption inputs."""

from __future__ import annotations

import pandas as pd

from core.models import Assumptions


class AssumptionAgent:
    """Perform additional validation on top of Pydantic constraints."""

    @staticmethod
    def validate(
        assumptions: Assumptions, historical: pd.DataFrame | None = None
    ) -> Assumptions:
        """Validate assumption plausibility."""

        if historical is not None:
            if "revenue" not in historical.columns:
                raise ValueError(
                    "Historical dataframe must include a 'revenue' column."
                )
            if (historical["revenue"] <= 0).any():
                raise ValueError("Historical revenues must be positive.")
            latest_revenue = float(historical["revenue"].iloc[-1])
            if assumptions.starting_revenue < latest_revenue * 0.5:
                raise ValueError(
                    "Starting revenue should be in line with recent history."
                )

        if assumptions.terminal_growth >= assumptions.wacc:
            raise ValueError("Terminal growth must remain below WACC.")

        return assumptions
