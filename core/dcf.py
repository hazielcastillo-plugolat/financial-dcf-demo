"""Deterministic DCF helper functions."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .models import Assumptions, ScenarioParams, ScenarioResult


@dataclass
class Projection:
    """Container for projected revenues and FCFF."""

    revenues: list[float]
    fcff: list[float]
    terminal_value: float


def _project_revenues(start: float, growth_rate: float, years: int) -> list[float]:
    revenues = []
    current = start
    for _ in range(1, years + 1):
        current *= 1 + growth_rate
        revenues.append(current)
    return revenues


def _calculate_fcff(assumptions: Assumptions, revenues: Sequence[float]) -> list[float]:
    fcff_values: list[float] = []
    for revenue in revenues:
        gross_profit = revenue * assumptions.gross_margin
        opex = revenue * assumptions.opex_pct
        ebit = gross_profit - opex
        nopat = ebit * (1 - assumptions.tax_rate)
        capex = revenue * assumptions.capex_pct
        delta_nwc = revenue * assumptions.delta_nwc_pct
        fcff = nopat - capex - delta_nwc
        fcff_values.append(fcff)
    return fcff_values


def _terminal_value(last_fcff: float, wacc: float, terminal_growth: float) -> float:
    if wacc <= terminal_growth:
        raise ValueError("Terminal value calculation requires WACC > terminal growth.")
    return last_fcff * (1 + terminal_growth) / (wacc - terminal_growth)


def _discount(values: Sequence[float], wacc: float) -> list[float]:
    return [value / (1 + wacc) ** (index + 1) for index, value in enumerate(values)]


def _npv(discounted_fcff: Sequence[float], discounted_terminal: float) -> float:
    return float(sum(discounted_fcff) + discounted_terminal)


def _irr(cash_flows: Sequence[float]) -> float | None:
    if not cash_flows:
        return None
    has_positive = any(value > 0 for value in cash_flows)
    has_negative = any(value < 0 for value in cash_flows)
    if not (has_positive and has_negative):
        return None

    rate = 0.1
    tolerance = 1e-6
    max_iterations = 100
    for _ in range(max_iterations):
        npv = 0.0
        derivative = 0.0
        for period, value in enumerate(cash_flows):
            discount = (1 + rate) ** period
            npv += value / discount
            if period > 0:
                derivative -= period * value / ((1 + rate) ** (period + 1))
        if abs(derivative) < 1e-9:
            break
        new_rate = rate - npv / derivative
        if abs(new_rate - rate) < tolerance:
            if new_rate > -0.999:
                return float(new_rate)
            return None
        rate = new_rate
    return None


def project_cash_flows(
    assumptions: Assumptions, scenario: ScenarioParams
) -> Projection:
    """Generate deterministic revenue and FCFF projections for a scenario."""

    revenues = _project_revenues(
        start=assumptions.starting_revenue,
        growth_rate=scenario.growth_rate,
        years=assumptions.years,
    )
    fcff_values = _calculate_fcff(assumptions, revenues)
    terminal = _terminal_value(
        fcff_values[-1], scenario.wacc, assumptions.terminal_growth
    )
    return Projection(revenues=revenues, fcff=fcff_values, terminal_value=terminal)


def run_dcf(assumptions: Assumptions, scenario: ScenarioParams) -> ScenarioResult:
    """Compute the DCF metrics for a scenario."""

    projection = project_cash_flows(assumptions, scenario)
    discounted_fcff = _discount(projection.fcff, scenario.wacc)
    discounted_terminal = (
        projection.terminal_value / (1 + scenario.wacc) ** assumptions.years
    )
    npv = _npv(discounted_fcff, discounted_terminal)
    # Negative initial outlay approximated as year-zero revenue investment
    initial_outlay = -assumptions.starting_revenue
    irr = _irr([initial_outlay, *projection.fcff, projection.terminal_value])
    return ScenarioResult(
        name=scenario.name,
        wacc=scenario.wacc,
        npv=npv,
        irr=irr,
        revenues=projection.revenues,
        fcff=projection.fcff,
        terminal_value=projection.terminal_value,
    )
