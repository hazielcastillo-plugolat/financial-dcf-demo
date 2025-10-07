"""Agent responsible for sourcing or synthesizing revenue data."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from core.models import Assumptions, Settings


class DataAgent:
    """Load revenue data from disk or generate a synthetic series."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.resolve_paths()

    def load_csv(self, relative_path: Path) -> pd.DataFrame:
        """Load a CSV file containing a revenue column."""

        path = (
            relative_path
            if relative_path.is_absolute()
            else self.settings.data_dir / relative_path
        )
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")
        df = pd.read_csv(path)
        if "revenue" not in df.columns:
            raise ValueError("CSV must contain a 'revenue' column.")
        return df

    def generate_synthetic(
        self, assumptions: Assumptions, periods: int = 5
    ) -> pd.DataFrame:
        """Create a simple synthetic revenue series anchored to the assumptions."""

        rng = np.random.default_rng(seed=42)
        base_revenue = assumptions.starting_revenue / (1 + assumptions.growth_rate)
        revenues = []
        current = base_revenue
        for _ in range(periods):
            noise = rng.normal(loc=0.0, scale=0.02)
            current *= 1 + assumptions.growth_rate + noise
            revenues.append(max(current, 0.0))
        df = pd.DataFrame(
            {
                "year": list(range(-periods + 1, 1)),
                "revenue": revenues,
            }
        )
        output_path = self.settings.data_dir / "synthetic_revenue.csv"
        df.to_csv(output_path, index=False)
        return df
