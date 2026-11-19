# Justfile for maintenance-wizard

set dotenv-load

default:
    @just --list

setup:
    uv sync --group dev
    uv run streamlit skills --yes
    mkdir -p .cursor/skills
    ln -sfn "$(readlink .agents/skills/developing-with-streamlit)" .cursor/skills/developing-with-streamlit

sync:
    uv sync --group dev

lint-check:
    uv run ruff check

format-check:
    uv run ruff format --check

lint:
    uv run ruff check --fix

format:
    uv run ruff format

test:
    uv run pytest

smoke-ui:
    uv run pytest -m holistic_ui_smoke

test-cov:
    uv run pytest --cov=maintenance_wizard --cov-report=html

link-secrets:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p .streamlit
    if [[ -f secrets.toml ]]; then
      ln -sf ../secrets.toml .streamlit/secrets.toml
      echo "Linked .streamlit/secrets.toml → secrets.toml"
    else
      echo "No secrets.toml at repo root — copy secrets.toml.example first" >&2
      exit 1
    fi

ui *ARGS:
    uv run streamlit run src/maintenance_wizard/ui/app.py --server.port 8765 {{ARGS}}

maintenance-ui *ARGS:
    @just ui {{ARGS}}

init-local-data:
    uv run python -m maintenance_wizard.scripts.seed_local_data

clean:
    find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
    find . -type d -name .pytest_cache -exec rm -r {} + 2>/dev/null || true
    find . -type d -name .mypy_cache -exec rm -r {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    rm -rf .coverage htmlcov/
    rm -rf dist/ build/ *.egg-info

check: lint-check format-check test

workflow-lint:
    uvx --from actionlint-py==1.7.12.25 actionlint

ci: sync workflow-lint lint-check format-check test

pre-commit:
    uv run pre-commit run --all-files

dev-setup: setup format lint test
    @echo "Development setup complete!"

migrate-xlsx *ARGS:
    uv run python -m maintenance_wizard.scripts.migrate_xlsx {{ARGS}}

import-completions *ARGS:
    uv run python -m maintenance_wizard.scripts.import_completions {{ARGS}}

rename-completions *ARGS:
    uv run python -m maintenance_wizard.scripts.rename_completions {{ARGS}}

notion-audit *ARGS:
    uv run python -m maintenance_wizard.scripts.notion_row_audit {{ARGS}}

purge-inactive-duplicates *ARGS:
    uv run python -m maintenance_wizard.scripts.purge_inactive_duplicates {{ARGS}}

info:
    @echo "Python version:"
    @uv run python --version
    @echo "\nPython location:"
    @uv run which python
