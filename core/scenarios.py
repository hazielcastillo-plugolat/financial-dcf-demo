"""Scenario expansion helpers."""

from __future__ import annotations

from .models import Assumptions, ScenarioParams


def build_scenarios(assumptions: Assumptions) -> list[ScenarioParams]:
    """Expand the base assumptions into base, optimistic, and pessimistic scenarios."""

    base = ScenarioParams(
        name="Base",
        growth_rate=assumptions.growth_rate,
        wacc=assumptions.wacc,
    )
    optimistic = ScenarioParams(
        name="Optimistic",
        growth_rate=assumptions.growth_rate + assumptions.optimistic_growth_delta,
        wacc=max(0.01, assumptions.wacc - assumptions.optimistic_wacc_delta),
    )
    pessimistic = ScenarioParams(
        name="Pessimistic",
        growth_rate=assumptions.growth_rate - assumptions.pessimistic_growth_delta,
        wacc=min(0.99, assumptions.wacc + assumptions.pessimistic_wacc_delta),
    )
    return [base, optimistic, pessimistic]
