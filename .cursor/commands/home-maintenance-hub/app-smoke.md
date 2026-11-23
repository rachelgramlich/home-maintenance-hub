---
name: app-smoke
description: Holistic headless + browser smoke before UI work is "done"
---

# App smoke (holistic sign-off)

**Purpose:** Catch production-only UI crashes before merge. Run this **before** claiming a UI PR is ready.

## Required: headless holistic smoke (CI-safe)

```bash
just smoke-ui
```

Same tests also run under **`just check`** / **`just ci`** (marker `holistic_ui_smoke`).

**Covers (local JSON store via pytest fixtures):**

- Import/load `src/home_maintenance_hub/ui/app.py` (no module-level `ImportError`)
- AppTest first run (hero, sidebar Refresh, open task Done button)

Implementation: `tests/ui/test_holistic_ui_smoke_apptest.py`, helpers in `tests/ui/ui_source.py`.

## Required for UI PRs: browser smoke

1. `just init-local-data`
2. `just ui` (port **8765**)
3. Confirm month board loads; toggle **Show done & won't do**; mark a task **Done** or **Won't do** on a throwaway month if needed (local JSON only)

## PR / chat sign-off lines

State **both**:

- **`Holistic smoke: ran`** (`just smoke-ui`) or **`Holistic smoke: skipped — <reason>`**
- **`Browser smoke: ran`**, **`Browser smoke: skipped — <reason>`**, or **`Browser smoke: N/A (non-UI)`**

See **`AGENTS.md`** → Manual verification.