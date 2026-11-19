# maintenance-wizard

**B & R Home Maintenance** — monthly checklist (**In progress** / **Done** / **Won't do**), overdue carry-over, contractors, details drawer. Notion-backed.

Repository: https://github.com/rachelgramlich/maintenance-wizard

- **v1:** Streamlit + **Notion** (three databases), or **local JSON** for dev/tests
- **v2:** Google Calendar reminders (not implemented yet)

Docs: [docs/FEATURES.md](docs/FEATURES.md) · [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Quick start (local)

```bash
brew install just uv   # if needed
git submodule update --init --recursive   # shared Cursor commands (rg-ai)
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
| `MAINTENANCE_WIZARD_TIMEZONE` | `America/New_York` | Month boundaries |

Local data file: `.local/maintenance_wizard/data.json` (gitignored).

## Notion (production)

Notion databases — [docs/NOTION_SETUP.md](docs/NOTION_SETUP.md). Connect **your** integration to the hub page, set `NOTION_API_KEY` + data source IDs in `.env`, then:

```bash
just migrate-xlsx --xlsx /path/to/Ocala.xlsx   # Home Maintenance tab
just migrate-xlsx --dry-run
```

Set `MAINTENANCE_WIZARD_STORE=notion` for production UI. Use **local** for offline dev/CI.

## Development

| Doc | Contents |
|-----|----------|
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Lint, tests, code review standards |
| [`AGENTS.md`](AGENTS.md) | Cursor agents and GitHub backlog workflow |

```bash
just check      # ruff check + format --check + pytest (same as CI)
just ci         # locked sync + workflow lint + same checks as check
just smoke-ui   # headless Streamlit smoke tests
just format
just pre-commit # all pre-commit hooks
```

### Cursor (optional)

Backlog: GitHub Issues (label `maintenance-wizard`). Follow [AGENTS.md](AGENTS.md). Slash commands under **`.cursor/commands/`** (shared via **rg-ai** submodule). Do not commit `.cursor/mcp.json`.