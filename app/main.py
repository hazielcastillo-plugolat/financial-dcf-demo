"""Streamlit entrypoint for the deterministic DCF demo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from pydantic import ValidationError

from agents.planner import Planner
from core.models import Assumptions, Results, Settings

st.set_page_config(page_title="Financial DCF Demo", layout="wide")

DEFAULT_ASSUMPTIONS: dict[str, Any] = {
    "starting_revenue": 1_200_000.0,
    "growth_rate": 0.08,
    "gross_margin": 0.45,
    "opex_pct": 0.25,
    "tax_rate": 0.21,
    "wacc": 0.1,
    "capex_pct": 0.05,
    "delta_nwc_pct": 0.03,
    "terminal_growth": 0.02,
    "years": 5,
    "optimistic_growth_delta": 0.03,
    "pessimistic_growth_delta": 0.02,
    "optimistic_wacc_delta": 0.01,
    "pessimistic_wacc_delta": 0.01,
}

if "assumption_values" not in st.session_state:
    st.session_state["assumption_values"] = DEFAULT_ASSUMPTIONS.copy()
if "historical_df" not in st.session_state:
    st.session_state["historical_df"] = None
if "results" not in st.session_state:
    st.session_state["results"] = None

settings = Settings()
settings.resolve_paths()
planner = Planner(settings)

tab_data, tab_assumptions, tab_results = st.tabs(
    ["Data", "Assumptions", "Run & Results"]
)


def _collect_assumptions() -> dict[str, Any]:
    return {key: st.session_state[key] for key in DEFAULT_ASSUMPTIONS}


with tab_data:
    st.subheader("Revenue Data")
    st.write(
        "Upload a CSV with a `revenue` column or generate synthetic data "
        "anchored to the current assumptions."
    )
    uploaded_file = st.file_uploader("Revenue CSV", type=["csv"], key="data_uploader")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.session_state["historical_df"] = df
        st.success("Loaded uploaded data.")

    if st.button("Generate synthetic data", key="generate_synthetic"):
        try:
            assumptions = Assumptions(**_collect_assumptions())
            synthetic = planner.data_agent.generate_synthetic(assumptions)
            st.session_state["historical_df"] = synthetic
            st.success(f"Generated synthetic data saved to {synthetic.shape[0]} rows.")
        except ValidationError as error:
            st.error(f"Cannot generate data: {error}")

    data_preview = st.session_state.get("historical_df")
    if data_preview is not None:
        st.caption("Data preview")
        st.dataframe(data_preview.tail(), use_container_width=True)


with tab_assumptions:
    st.subheader("Projection Assumptions")
    cols = st.columns(3)
    numeric_fields = [
        ("starting_revenue", "Starting revenue", 100_000.0, 10_000_000.0, 50_000.0),
        ("growth_rate", "Growth rate", -0.2, 0.5, 0.01),
        ("gross_margin", "Gross margin", 0.1, 0.9, 0.01),
        ("opex_pct", "Opex %", 0.05, 0.6, 0.01),
        ("tax_rate", "Tax rate", 0.0, 0.5, 0.01),
        ("wacc", "WACC", 0.03, 0.25, 0.005),
        ("capex_pct", "Capex %", 0.0, 0.2, 0.005),
        ("delta_nwc_pct", "Δ NWC %", -0.1, 0.2, 0.005),
        ("terminal_growth", "Terminal growth", -0.02, 0.08, 0.005),
    ]
    for index, (field, label, min_value, max_value, step) in enumerate(numeric_fields):
        column = cols[index % len(cols)]
        column.number_input(
            label,
            min_value=float(min_value),
            max_value=float(max_value),
            step=float(step),
            value=float(st.session_state["assumption_values"][field]),
            key=field,
        )

    st.slider(
        "Projection years",
        min_value=3,
        max_value=10,
        value=int(st.session_state["assumption_values"]["years"]),
        key="years",
    )

    st.markdown("#### Scenario deltas")
    delta_cols = st.columns(2)
    delta_cols[0].number_input(
        "Optimistic growth delta",
        min_value=0.0,
        max_value=0.2,
        step=0.005,
        value=float(st.session_state["assumption_values"]["optimistic_growth_delta"]),
        key="optimistic_growth_delta",
    )
    delta_cols[0].number_input(
        "Optimistic WACC delta",
        min_value=0.0,
        max_value=0.1,
        step=0.002,
        value=float(st.session_state["assumption_values"]["optimistic_wacc_delta"]),
        key="optimistic_wacc_delta",
    )
    delta_cols[1].number_input(
        "Pessimistic growth delta",
        min_value=0.0,
        max_value=0.2,
        step=0.005,
        value=float(st.session_state["assumption_values"]["pessimistic_growth_delta"]),
        key="pessimistic_growth_delta",
    )
    delta_cols[1].number_input(
        "Pessimistic WACC delta",
        min_value=0.0,
        max_value=0.1,
        step=0.002,
        value=float(st.session_state["assumption_values"]["pessimistic_wacc_delta"]),
        key="pessimistic_wacc_delta",
    )

    st.info("Use the controls above to fine-tune the assumptions for all scenarios.")


with tab_results:
    st.subheader("Run Pipeline & Review Outputs")
    run_clicked = st.button("Run pipeline", type="primary", use_container_width=False)
    if run_clicked:
        try:
            assumptions = Assumptions(**_collect_assumptions())
            data_df = st.session_state.get("historical_df")
            pipeline_results = planner.run_pipeline(
                assumptions, historical_df=data_df
            )
            st.session_state["results"] = pipeline_results
            st.success("Pipeline completed successfully.")
        except ValidationError as error:
            st.error(f"Validation error: {error}")
        except ValueError as error:
            st.error(f"Pipeline failed: {error}")

    stored_results: Results | None = st.session_state.get("results")
    if stored_results is not None:
        st.markdown("#### Scenario summary")
        scenario_records = [
            {
                "Scenario": scenario.name,
                "WACC": scenario.wacc,
                "NPV": scenario.npv,
                "IRR": scenario.irr if scenario.irr is not None else "n/a",
            }
            for scenario in stored_results.scenarios
        ]
        summary_df = pd.DataFrame(scenario_records)
        st.dataframe(summary_df, use_container_width=True)

        csv_data = summary_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download scenario summary CSV",
            data=csv_data,
            file_name="scenario_summary.csv",
            mime="text/csv",
        )

        st.markdown("#### FCFF by scenario")
        fcff_df = pd.DataFrame(stored_results.fcff_table)
        st.dataframe(fcff_df, use_container_width=True)

        st.markdown("#### WACC sensitivity")
        sensitivity_df = pd.DataFrame(
            [point.dict() for point in stored_results.sensitivity]
        )
        st.line_chart(sensitivity_df, x="wacc", y="npv")

        plot_path = stored_results.artifacts.get("sensitivity_plot")
        if plot_path and Path(plot_path).exists():
            st.image(plot_path, caption="Sensitivity curve", use_column_width=True)

        st.markdown("#### Artifacts")
        for label, path in stored_results.artifacts.items():
            st.write(f"- **{label}**: `{path}`")
