PYTHON ?= python

.PHONY: install format lint typecheck test dev

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

format:
	$(PYTHON) -m black .

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy .

test:
	$(PYTHON) -m pytest -q

dev:
	streamlit run app/main.py
