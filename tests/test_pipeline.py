from pathlib import Path

from agents.planner import Planner
from core.models import Assumptions, Settings


def test_pipeline_smoke(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "artifacts",
    )
    planner = Planner(settings)
    assumptions = Assumptions(
        starting_revenue=900_000,
        growth_rate=0.07,
        gross_margin=0.48,
        opex_pct=0.28,
        tax_rate=0.21,
        wacc=0.1,
        capex_pct=0.05,
        delta_nwc_pct=0.02,
        terminal_growth=0.02,
        years=5,
        optimistic_growth_delta=0.02,
        pessimistic_growth_delta=0.015,
        optimistic_wacc_delta=0.01,
        pessimistic_wacc_delta=0.015,
    )
    results = planner.run_pipeline(assumptions)
    assert len(results.scenarios) == 3
    assert results.fcff_table
    for artifact_path in results.artifacts.values():
        assert Path(artifact_path).exists()
