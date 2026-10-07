.PHONY: install test test-cov lint format typecheck check run doctor clean
PYTHON ?= python3
VENV := .venv
BIN := $(VENV)/bin

install:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -e ".[dev]"

test:
	$(BIN)/python -m pytest -q

test-cov:
	$(BIN)/python -m pytest -q --cov=sol_lite --cov-report=term-missing

lint:
	$(BIN)/ruff check src tests

format:
	$(BIN)/ruff format src tests

typecheck:
	$(BIN)/mypy src

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

run:
	$(BIN)/python -m sol_lite

doctor:
	$(BIN)/python -m sol_lite doctor

clean:
	find . -type d \( -name "__pycache__" -o -name ".pytest_cache" -o -name ".mypy_cache" -o -name ".ruff_cache" \) -prune -exec rm -rf {} +
