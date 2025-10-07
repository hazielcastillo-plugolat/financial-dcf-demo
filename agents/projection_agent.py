"""Agent computing DCF projections per scenario."""

from __future__ import annotations

from collections.abc import Iterable

from core.dcf import run_dcf
from core.models import Assumptions, ScenarioParams, ScenarioResult


class ProjectionAgent:
    """Compute the valuation metrics for each scenario."""

    def run(
        self, assumptions: Assumptions, scenarios: Iterable[ScenarioParams]
    ) -> list[ScenarioResult]:
        """Return scenario-level DCF results."""

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            results.append(run_dcf(assumptions, scenario))
        return results
