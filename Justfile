set dotenv-load

default:
    @just --list

setup:
    uv sync --group dev

sync:
    uv sync --group dev

lint:
    uv run ruff check --fix

format:
    uv run ruff format

test:
    uv run pytest

check: lint test

ui *ARGS:
    uv run streamlit run src/maintenance_wizard/ui/app.py --server.port 8765 {{ARGS}}

init-local-data:
    uv run python -m maintenance_wizard.scripts.seed_local_data

clean:
    find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -r {} + 2>/dev/null || true