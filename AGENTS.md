# Agent instructions (home_maintenance_hub)

## Issues (slash commands = primary UX)

| You type | Purpose |
| --- | --- |
| **`/create-issues`** | One or more notes → auto **bug vs backlog**, merge by **code area**, create GitHub issue(s) via **`gh`** |
| **`/app-review`** | Hands-on Streamlit UAT → findings → optional grouped **`gh`** issues (`.cursor/commands/home-maintenance-hub/app-review.md`) |
| **`/app-smoke`** | Holistic headless + browser sign-off before UI work is done (`.cursor/commands/home-maintenance-hub/app-smoke.md`) |
| **`/architecture-review`** | Standards audit + optional **`audit`** issues (shared: `.cursor/commands/shared/architecture-review.md`) |
| **`/list-enhancements`** | Open backlog (`home-maintenance-hub` label) via **`gh`** (`.cursor/commands/home-maintenance-hub/list-enhancements.md`) |
| **`/work-on-issue N`** | Implement one issue — area → files and UAT rules **below** + shared `.cursor/commands/shared/work-on-issue.md` |
| **`/tidy-project`** | Repo-wide structure-only tidy PR(s) (shared: `.cursor/commands/shared/tidy-project.md`) |
| **`/create-command`** | Add slash command or skill without name collisions (shared: `.cursor/commands/shared/create-command.md`) |
| *(automatic)* **`tidy-first` skill** | While implementing work: tidy inline, **S** vs **B** in separate commits |

**Layout:** [rg-ai](https://github.com/rachelgramlich/rg-ai) **git submodule** at **`.cursor/rg-ai`** (private). Shared slash files via **`.cursor/commands/shared/`** → `.cursor/rg-ai/.cursor/commands`. Maintenance-only commands in **`.cursor/commands/home-maintenance-hub/`**. After clone or new worktree: **`git submodule update --init --recursive`** once if `/` doesn’t list shared commands — **your Mac only**; GitHub Actions sets **`submodules: false`** (see `.github/workflows/ci.yml`) because `just ci` does not need rg-ai.

### Labels and areas (for `/create-issues`, `/work-on-issue`)

| Item | Value |
| --- | --- |
| **Backlog label** | `home-maintenance-hub` |
| **Bug label** | `bug` |
| **Area labels** | `mw-area-ui`, `mw-area-store`, `mw-area-domain`, `mw-area-notion`, `mw-area-other` |
| **List backlog** | **`/list-enhancements`** or `gh issue list --label home-maintenance-hub --state open` |
| **Verify** | `just check` (includes holistic UI smoke tests) |
| **Holistic UI smoke** | `just smoke-ui` (headless AppTest; local JSON store in CI) |

**Enhancement create example:** `gh issue create … --label home-maintenance-hub --label mw-area-ui` with template sections **Description**, **Expected behavior & manual test hints**, **Area**.

**Area → files (read first):**

| Area | Files |
| --- | --- |
| **ui** | `src/home_maintenance_hub/ui/app.py`, `styles.py`, `theme.py`, `static/app_theme.css` |
| **store** | `src/home_maintenance_hub/store/` |
| **domain** | `src/home_maintenance_hub/domain/` |
| **notion** | `docs/NOTION_SETUP.md` (integration TBD in code) |
| **other** | skim issue + grep |

Area from label `mw-area-<name>` or `### Area` in the issue body.

### Manual verification (UI issues, for `/work-on-issue`)

**Before claiming done / opening a UI PR:** run **`just smoke-ui`** (or full **`just check`**).

**Local preflight:**

```bash
just init-local-data && PYTHONPATH=src uv run python -c "from home_maintenance_hub.config import get_settings; get_settings(); print('config ok')"
```

**Browser smoke:** with **notion** store, start **`just ui`** and walk month picker, filters, Done / Won't do against your workspace. Default **local** store: confirm task cards render after `just init-local-data`.

State in chat and PR:

- **`Holistic smoke: ran`** (`just smoke-ui`), **`Holistic smoke: skipped — <reason>`**, or **`Holistic smoke: N/A (non-UI)`**
- **`Browser smoke: ran`**, **`Browser smoke: skipped — <reason>`**, or **`Browser smoke: N/A (non-UI)`**

### Backlog ship checklist (enhancements)

1. PR title: `#<issue-number>: <issue title>`
2. PR template **Manual verification** + `Closes #<issue-number>`
3. Create PRs **ready for review** unless the user asks for a draft.
4. Non-UI → agent runs `just check` and posts sign-off via **`gh pr comment`**; UI → **`just smoke-ui`** before PR ready.

Do not close backlog issues by hand — merge with `Closes #N`.

## User workflow

Run **`just ui`** (or **`just maintenance-ui`**) for the monthly maintenance board. Local dev: **`just init-local-data`** once.

After **`just setup`**, `.cursor/skills/developing-with-streamlit` symlinks from Streamlit skills. **`tidy-first`** is under `.cursor/skills/`. **`/tidy-project`** is shared under `.cursor/commands/shared/`.

## No backward-compatibility shims (default)

When removing a field, API, or Notion property, **delete the code and schema in the same change** — do not keep empty parsers, unused model fields, or “we still read it but ignore it” paths.

- Prefer a **one-shot migration** (script, Notion backfill, or rewrite on next load) over leaving dormant branches.
- Update **fixtures, seed data, and docs** in the same PR.
- Ask the owner before keeping a compatibility path only if external consumers still depend on it (this household app usually does not).

## Structure-only tidy (agents)

- **S vs B:** **`tidy-first`** skill — structure (**S**) and behavior (**B**) in **separate commits**. Repo-wide → **`/tidy-project`**.
- **Verify before push:** `just check` → `ruff check`, `ruff format --check`, `pytest`.
- **CI:** GitHub Actions runs `just ci` on every PR.
- **UI tests:** `tests/ui/ui_source.py` for `APP_PATH` / `ui_source()` — no ad-hoc path literals in tests.

**Requires `gh`** authenticated for this repo when filing or shipping backlog issues.

## Agent delivery default

After **substantive** implementation (not Q&A-only): run checks → commit → push → **open a PR** (`gh pr create`). Do not wait for the user to ask for a PR — include the PR link in your final message. See `.cursor/rules/always-open-pr.mdc`.