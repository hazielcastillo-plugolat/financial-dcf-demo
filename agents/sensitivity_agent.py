"""Agent generating WACC sensitivity analysis assets."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.dcf import run_dcf
from core.models import Assumptions, ScenarioParams, SensitivityPoint, Settings


class SensitivityAgent:
    """Produce a one-dimensional WACC sensitivity table and plot."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.resolve_paths()

    def run(
        self, assumptions: Assumptions, scenario: ScenarioParams
    ) -> tuple[list[SensitivityPoint], dict[str, str]]:
        """Sweep WACC values around the scenario baseline."""

        start = max(0.02, scenario.wacc - 0.04)
        stop = min(0.3, scenario.wacc + 0.04)
        wacc_values = np.round(np.arange(start, stop + 0.0001, 0.005), decimals=3)

        points: list[SensitivityPoint] = []
        for wacc in wacc_values:
            params = ScenarioParams(
                name=scenario.name, growth_rate=scenario.growth_rate, wacc=float(wacc)
            )
            result = run_dcf(assumptions, params)
            points.append(SensitivityPoint(wacc=float(wacc), npv=result.npv))

        artifacts = self._persist(points)
        return points, artifacts

    def _persist(self, points: list[SensitivityPoint]) -> dict[str, str]:
        df = pd.DataFrame([point.dict() for point in points])
        csv_path = self.settings.output_dir / "sensitivity_wacc.csv"
        df.to_csv(csv_path, index=False)

        plot_path = self.settings.output_dir / "sensitivity_wacc.png"
        self._plot(df, plot_path)

        return {
            "sensitivity_csv": str(csv_path),
            "sensitivity_plot": str(plot_path),
        }

    @staticmethod
    def _plot(df: pd.DataFrame, output_path: Path) -> None:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(df["wacc"], df["npv"], marker="o")
        ax.set_xlabel("WACC")
        ax.set_ylabel("NPV")
        ax.set_title("NPV Sensitivity to WACC")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        fig.tight_layout()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
