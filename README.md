# financial-dcf-demo

Minimal deterministic discounted cash flow demo that highlights agent-like orchestration with a Streamlit UI. The project stays offline, uses local CSV inputs or synthetic data, and produces valuation metrics, scenario tables, and WACC sensitivity outputs.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
cp .env.example .env
make install
make test
make dev  # launches Streamlit at http://localhost:8501
```

## How It Works

- **Data tab** – Upload a CSV containing a `revenue` column or generate a synthetic history anchored to the current assumptions.
- **Assumptions tab** – Configure base revenue, cost structure, capital assumptions, and scenario deltas.
- **Run & Results tab** – Execute the pipeline to review NPV/IRR per scenario, FCFF tables, and the WACC sensitivity chart. Download the scenario summary and find generated CSVs/plots under `./artifacts`.

Environment variables are loaded via `.env` (see `.env.example`) and control where inputs and outputs are stored:

- `DATA_DIR` – directory for uploaded or synthetic CSVs (defaults to `./data`)
- `OUTPUT_DIR` – directory where all artifacts are written (defaults to `./artifacts`)

## Architecture

The app is intentionally split into small, single-purpose agents coordinated by a planner:

| Component | Responsibility |
| --- | --- |
| `DataAgent` | Load CSV data or generate a synthetic revenue series. |
| `AssumptionAgent` | Apply extra validation on top of Pydantic checks. |
| `ProjectionAgent` | Run DCF calculations per scenario. |
| `SensitivityAgent` | Sweep WACC values, produce a table, and render a plot. |
| `ReportAgent` | Persist CSV artifacts and assemble the final results payload. |
| `Planner` | Orchestrate the agents into a deterministic pipeline. |

Core utilities in `core/` cover Pydantic models, scenario expansion, and deterministic DCF math.

## Extending The Demo

- **Add a new agent** – Implement the agent in `agents/`, inject it into the `Planner`, and extend the results model with its outputs.
- **Support new inputs** – Update `core/models.Assumptions`, add validation logic, and surface the inputs in the Streamlit UI.
- **Modify projections** – Extend `core/dcf.py` with additional line items or alternative terminal value logic.

## Tooling

- `black`, `ruff`, `mypy`, and `pytest` wired via `make` targets and GitHub Actions (`.github/workflows/ci.yml`).
- `pytest` covers DCF calculations, scenario expansion, and an end-to-end pipeline smoke test.
- `Makefile` includes commands for installation, formatting, linting, type checking, testing, and running the Streamlit app.

