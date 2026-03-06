#!/bin/bash
set -e
echo "--- Syncing Environment ---"
uv sync --all-extras
echo "--- Linting (Ruff) ---"
uv run ruff check . --fix
echo "--- Typing (Mypy) ---"
uv run mypy . --strict
echo "--- Testing (Pytest) ---"
uv run pytest --cov=src --cov-report=term-missing
