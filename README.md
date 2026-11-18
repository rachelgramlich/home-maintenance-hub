# Maintenance Wizard

Monthly home maintenance checklist: **Done** / **Won’t do**, overdue carry-over, last-done notes.

- **v1:** Streamlit + hidden **Google Sheet** (or **local JSON** for dev)
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
| `MAINTENANCE_WIZARD_STORE` | `local` | `local` or `google_sheets` |
| `MAINTENANCE_WIZARD_SHEET_ID` | — | Google spreadsheet ID |
| `MAINTENANCE_WIZARD_TIMEZONE` | `America/New_York` | Month/due boundaries |
| `MAINTENANCE_WIZARD_DUE_SOON_DAYS` | `7` | Orange “due soon” window |

Local data file: `.local/maintenance_wizard/data.json` (gitignored).

## Google Sheets (production)

1. Create a spreadsheet with tabs **`templates`** and **`completions`** (headers match [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)).
2. OAuth token at `.local/maintenance_wizard/token.json` (setup script coming in a follow-up).
3. Set `MAINTENANCE_WIZARD_STORE=google_sheets` and `MAINTENANCE_WIZARD_SHEET_ID`.

## Development

```bash
just check    # ruff + pytest
just format
```