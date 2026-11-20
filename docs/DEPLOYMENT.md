# Deployment — Streamlit Cloud (v1)

Household production target: **Streamlit Community Cloud** with **Notion** as the data store (no Google Sheets).

**Operations runbook (auth, feedback PAT, smoke):** [operations/household-deploy.md](operations/household-deploy.md).

## Prerequisites

1. Notion hub + three databases — [NOTION_SETUP.md](NOTION_SETUP.md).
2. A Notion **internal integration** connected to the hub page (same token the app uses).
3. GitHub repo `rachelgramlich/maintenance-wizard` (or your fork) with CI green on `main`.

## Streamlit Cloud app

1. [Share.streamlit.io](https://share.streamlit.io/) → **New app**.
2. Repository: this repo; branch: `main`.
3. **Main file path:** `src/maintenance_wizard/ui/app.py`
4. **Python version:** 3.12 (match `pyproject.toml`).

Streamlit reads secrets from **Secrets** in the app settings (TOML). Copy from [`secrets.toml.example`](../secrets.toml.example):

```toml
MAINTENANCE_WIZARD_STORE = "notion"
MAINTENANCE_WIZARD_TIMEZONE = "America/New_York"

NOTION_API_KEY = "secret_…"
MAINTENANCE_WIZARD_NOTION_TASKS_DS_ID = "collection://…"
MAINTENANCE_WIZARD_NOTION_CONTRACTORS_DS_ID = "collection://…"
MAINTENANCE_WIZARD_NOTION_COMPLETIONS_DS_ID = "collection://…"
```

Data source IDs may use the `collection://` prefix or the bare UUID (the app strips the prefix).

## Dependencies

Cloud installs from `pyproject.toml` via the default Streamlit dependency resolver. Local parity:

```bash
uv sync
```

If Cloud cannot resolve the project file, add a root `requirements.txt` generated from `uv export` (optional; not required when `pyproject.toml` is at repo root).

## Access control (v1)

Streamlit Cloud **private** apps limit viewers to users you invite. Google OAuth allowlist (grocery-wizard parity) is **not** in v1 scope — use private app + shared household logins, or revisit in a follow-up issue.

## Smoke test after deploy

1. Open the deployed URL — hero **B & R Home Maintenance** and month metrics load.
2. Toggle **Refresh** — no error banner.
3. Mark a low-risk task **In progress**, then revert or complete in Notion if needed.
4. **Manage contractors** → add/edit smoke (optional).

## Local production dry-run

```bash
export MAINTENANCE_WIZARD_STORE=notion
# NOTION_* from .env
just ui
```

## Migration & data hygiene

| Command | Purpose |
|---------|---------|
| `just migrate-xlsx --xlsx PATH [--apply-cadence-dedupe]` | Templates from Ocala xlsx |
| `just import-completions` (default year = current calendar year) | Backfill completions from checklist screenshots |
| `just rename-completions [--dry-run]` | Retitle existing completion rows after task renames |
| `just purge-inactive-duplicates [--dry-run]` | Archive inactive slot rows + orphan completion rows |

After cadence dedupe, run `purge-inactive-duplicates` so the Notion task board does not show deactivated duplicate rows.