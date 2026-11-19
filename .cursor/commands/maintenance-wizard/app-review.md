---
name: app-review
description: Hands-on Streamlit app review → findings report → grouped GitHub issues via gh
---

# App review (UAT through issue filing)

**Scope:** Manually exercise the **Maintenance Wizard Streamlit UI**, return a structured findings report, and (when the user asks) file grouped GitHub issues. **Do not implement fixes** unless the user asks after issues exist.

**Chained workflow:** Findings → **`.cursor/commands/shared/create-issues.md`** (bug/backlog rules, labels, `gh` usage).

## Prerequisites

- Repo root workspace; local store via **`just init-local-data`** (default) or configured backend.
- **`gh`** authenticated when filing issues.
- Read **`.cursor/skills/developing-with-streamlit/SKILL.md`** when interpreting Streamlit behavior.

## Surfaces to cover

| Surface | Minimum path |
| --- | --- |
| **Month board** | Year/month pickers, area filter, overdue vs open metrics |
| **Task cards** | Done / Won't do, notes field, refresh after completion |
| **Sidebar** | Refresh clears cache; show/hide closed tasks |

Start with **`just ui`**. Use browser automation for hands-on UAT.

## Findings report (required before issues)

Deliver: **Summary**, **Blocking**, **Non-blocking**, **Nice-to-have** — each bullet specific (steps + observed behavior).

## Filing issues

Group related findings. Use **`/create-issues`** or **`gh issue create`** with label **`maintenance-wizard`** and **`mw-area-ui`** when appropriate.

Do not implement fixes in the same turn unless the user explicitly asks.