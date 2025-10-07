from core.models import Assumptions
from core.scenarios import build_scenarios


def test_three_scenarios_created() -> None:
    assumptions = Assumptions(
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
        optimistic_growth_delta=0.01,
        pessimistic_growth_delta=0.02,
        optimistic_wacc_delta=0.005,
        pessimistic_wacc_delta=0.01,
    )
    scenarios = build_scenarios(assumptions)
    assert len(scenarios) == 3
    base, optimistic, pessimistic = scenarios
    assert base.growth_rate == assumptions.growth_rate
    assert optimistic.growth_rate > base.growth_rate
    assert pessimistic.growth_rate < base.growth_rate
    assert optimistic.wacc < base.wacc
    assert pessimistic.wacc > base.wacc
