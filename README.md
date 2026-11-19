# maintenance-wizard

**B & R Home Maintenance** — monthly checklist (**In progress** / **Done** / **Won’t do**), overdue carry-over, contractors, details drawer. Notion-backed.

Repository: https://github.com/rachelgramlich/maintenance-wizard

- **v1:** Streamlit + **Notion** (three databases), or **local JSON** for dev/tests
- **v2:** Google Calendar reminders (not implemented yet)

Docs: [docs/FEATURES.md](docs/FEATURES.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Quick start (local)

```bash
brew install just uv   # if needed
just setup
just init-local-data
just ui
```

Open http://127.0.0.1:8765

## Configuration

Copy `.env.example` → `.env` or `secrets.toml.example` → `secrets.toml`.

| Variable | Default | Meaning |
|----------|---------|---------|
| `MAINTENANCE_WIZARD_STORE` | `local` | `local` or `notion` |
| `NOTION_API_KEY` | — | Notion integration token |
| `MAINTENANCE_WIZARD_NOTION_*_DS_ID` | — | Data source IDs (tasks, contractors, completions) |
| `MAINTENANCE_WIZARD_TIMEZONE` | `America/New_York` | Month/due boundaries |
| `MAINTENANCE_WIZARD_DUE_SOON_DAYS` | `7` | Orange “due soon” window |

Local data file: `.local/maintenance_wizard/data.json` (gitignored).

## Notion (production)

Notion databases already exist — [docs/NOTION_SETUP.md](docs/NOTION_SETUP.md). Connect **your** integration to the hub page, set `NOTION_API_KEY` + data source IDs in `.env`, then run `just migrate-xlsx` (when implemented).

## Development

```bash
just check    # ruff + pytest
just format
```