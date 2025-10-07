"""Pydantic data models for the DCF demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, BaseSettings, Field, validator
from pydantic.fields import ModelField


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    data_dir: Path = Field(default=Path("./data"))
    output_dir: Path = Field(default=Path("./artifacts"))

    class Config:
        env_prefix = ""
        env_file = ".env"
        env_file_encoding = "utf-8"

    def resolve_paths(self) -> None:
        """Ensure the configured directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


class Assumptions(BaseModel):
    """High-level financial assumptions used across scenarios."""

    starting_revenue: float = Field(gt=0, description="Base revenue in year 0.")
    growth_rate: float = Field(ge=-0.5, le=1.0, description="Annual revenue growth.")
    gross_margin: float = Field(gt=0, lt=1, description="Gross margin percentage.")
    opex_pct: float = Field(
        gt=0, lt=1, description="Operating expenses as % of revenue."
    )
    tax_rate: float = Field(ge=0, lt=1, description="Effective tax rate.")
    wacc: float = Field(gt=0, lt=1, description="Weighted average cost of capital.")
    capex_pct: float = Field(
        ge=0, lt=1, description="Capital expenditures as % of revenue."
    )
    delta_nwc_pct: float = Field(
        ge=-1, lt=1, description="Change in net working capital as % of revenue."
    )
    terminal_growth: float = Field(
        ge=-0.05, lt=0.2, description="Terminal growth rate."
    )
    years: int = Field(default=5, ge=1, le=10, description="Projection horizon.")
    optimistic_growth_delta: float = Field(default=0.02, ge=0, le=0.2)
    pessimistic_growth_delta: float = Field(default=0.02, ge=0, le=0.2)
    optimistic_wacc_delta: float = Field(default=0.01, ge=0, le=0.1)
    pessimistic_wacc_delta: float = Field(default=0.01, ge=0, le=0.1)

    @validator("wacc")
    def validate_wacc(cls, value: float, values: dict[str, Any]) -> float:
        terminal_growth = values.get("terminal_growth", 0.0)
        if value <= terminal_growth:
            raise ValueError("WACC must be greater than terminal growth rate.")
        return value

    @validator("gross_margin", "opex_pct")
    def validate_margin_sum(
        cls, value: float, values: dict[str, Any], field: ModelField
    ) -> float:
        gross_margin = values.get(
            "gross_margin", 0.0 if field.name == "gross_margin" else value
        )
        opex_pct = values.get("opex_pct", 0.0 if field.name == "opex_pct" else value)
        if gross_margin and opex_pct and (gross_margin + opex_pct) >= 0.99:
            raise ValueError(
                "Gross margin plus opex percentage should leave room for profit."
            )
        return value


class ScenarioParams(BaseModel):
    """Scenario-specific adjustments derived from base assumptions."""

    name: str
    growth_rate: float
    wacc: float

    @validator("growth_rate")
    def validate_growth(cls, value: float) -> float:
        if value < -0.5:
            raise ValueError("Growth rate is unrealistically low for scenario.")
        return value

    @validator("wacc")
    def validate_wacc(cls, value: float) -> float:
        if value <= 0 or value >= 1:
            raise ValueError("WACC must be between 0 and 1.")
        return value


class ScenarioResult(BaseModel):
    """DCF metrics computed for a single scenario."""

    name: str
    wacc: float
    npv: float
    irr: float | None
    revenues: list[float]
    fcff: list[float]
    terminal_value: float


class SensitivityPoint(BaseModel):
    """Single point in the WACC sensitivity curve."""

    wacc: float
    npv: float


class Results(BaseModel):
    """Full pipeline output passed back to the UI layer."""

    scenarios: list[ScenarioResult]
    sensitivity: list[SensitivityPoint]
    fcff_table: list[dict[str, float | int]]
    artifacts: dict[str, str]
    data_preview: list[dict[str, float | int]]
