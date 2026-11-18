# Architecture decision (current)

**Chosen direction:** Small **Python / Streamlit** repo developed in **Cursor**, **hidden Google Sheet** as data store. **v1:** monthly checklist only. **v2:** Google Calendar sync + reminders. **Notion not required.**

**Rejected for v1:** Apps Script–first, paid apps, Zapier/Make, GCal, explicit Defer action (month-end rollover instead).

See [FEATURES.md](./FEATURES.md) for v1/v2 scope.

---

## What “last time I did X” means (product)

You want **lookup**, not a buried audit log:

- On each task (monthly view or detail): **Last completed:** date, optional **notes**, optional **vendor/cost** later.
- Implemented by:
  - **`instances` sheet:** one row per task per period; when status → Done, set `completed_on` and `notes`.
  - **`last_done` in UI:** query latest instance per `task_id` where `status = Done` (or `Won't do` if you want that visible — default: Done only).

No separate “query vs save” choice — **saving each completion with notes automatically enables “last time”** in the app.

---

## Data model (Google Sheet — three tabs)

| Tab | Role |
|-----|------|
| **templates** | Stable task definitions + `gcal_series_id` |
| **instances** | Per-month state (`pending` / `done` / `wont_do`); month-end rolls unmarked `pending` forward as **carried_over** |
| **history** (optional) | Append-only copy on action for extra safety; can skip if instances are never hard-deleted |

**templates columns (minimum):** `task_id`, `name`, `cadence`, `due_month`, `due_day`, `area`, `active` (+ `gcal_series_id` in **v2**)

**instances columns (minimum):** `instance_id`, `task_id`, `period_key` (`YYYY-MM`), `status`, `due_date`, `carried_over`, `completed_on`, `notes` (+ `gcal_instance_id` in **v2**)

### Month rollover (v1)

When the calendar month ends, any instance still `pending` for month *M* is closed as implicit defer: create or activate `pending` + `carried_over=true` for month *M+1* (or run this on first open of the new month).

---

## Why Streamlit repo, not Apps Script (Cursor + “you do it”)

| Concern | Apps Script web app | Streamlit repo (this project) |
|---------|---------------------|-------------------------------|
| Build & test in Cursor / cloud agent | Weak — deploy/authorize in Google UIs, awkward local run | **Strong** — same as grocery-wizard |
| Iteration with AI | Edit in browser or `clasp` sync | **Edit in repo, `just ui`, pytest** |
| Your manual config | Many Google Cloud / deploy steps | **One-time secrets** (below), then agent maintains code |
| Partner | GCal subscribe | Same — **GCal only** |

Apps Script is fine for solo tinkering; it is a poor fit for **“the agent implements everything in this workspace.”**

---

## One-time manual setup

**v1:** Google Cloud + **Sheets API** only; OAuth once; `just init-sheet` creates the workbook.

**v2 adds:** Calendar API, dedicated calendar ID, sync job.

Optional later: Streamlit Community Cloud secrets (same TOML as grocery-wizard).

---

## Migration A → B

Not applicable if we **start** with Streamlit + Sheet. The earlier Apps Script path was an optional phase-1; we skip it to match Cursor-first delivery.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-11-17 | Lock Streamlit + Sheet + GCal; per-task last-done + notes; Cursor-first |
| 2026-11-17 | v1 monthly only; done/won’t do; auto month rollover; GCal → v2 |