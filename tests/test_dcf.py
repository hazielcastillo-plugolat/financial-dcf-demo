from core.dcf import run_dcf
from core.models import Assumptions, ScenarioParams


def base_assumptions() -> Assumptions:
    return Assumptions(
        starting_revenue=1_000_000,
        growth_rate=0.08,
        gross_margin=0.5,
        opex_pct=0.3,
        tax_rate=0.21,
        wacc=0.1,
        capex_pct=0.05,
        delta_nwc_pct=0.02,
        terminal_growth=0.02,
        years=5,
        optimistic_growth_delta=0.02,
        pessimistic_growth_delta=0.02,
        optimistic_wacc_delta=0.01,
        pessimistic_wacc_delta=0.01,
    )


def test_npv_positive_under_reasonable_inputs() -> None:
    assumptions = base_assumptions()
    scenario = ScenarioParams(
        name="Base", growth_rate=assumptions.growth_rate, wacc=assumptions.wacc
    )
    result = run_dcf(assumptions, scenario)
    assert result.npv > 0
    assert result.irr is None or result.irr > -1


def test_npv_decreases_with_higher_wacc() -> None:
    assumptions = base_assumptions()
    low_wacc = ScenarioParams(
        name="Low", growth_rate=assumptions.growth_rate, wacc=0.08
    )
    high_wacc = ScenarioParams(
        name="High", growth_rate=assumptions.growth_rate, wacc=0.14
    )
    low_result = run_dcf(assumptions, low_wacc)
    high_result = run_dcf(assumptions, high_wacc)
    assert low_result.npv > high_result.npv
