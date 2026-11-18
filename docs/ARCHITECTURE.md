# Maintenance Wizard — architecture

**Repo:** `maintenance-wizard` · **Package:** `maintenance_wizard`

**Chosen direction:** Small **Python / Streamlit** repo developed in **Cursor**, **hidden Google Sheet** as data store. **v1:** monthly checklist only. **v2:** Google Calendar sync + reminders. **Notion not required.**

**Rejected for v1:** Apps Script–first, paid apps, Zapier/Make, GCal, explicit Defer action (month-end rollover instead).

See [FEATURES.md](./FEATURES.md) for v1/v2 scope.

---

## What “last time I did X” means (product)

You want **lookup**, not a buried audit log:

- On each task (monthly view or detail): **Last completed:** date, optional **notes**, optional **vendor/cost** later.
- Implemented by **`completions` tab:** append a row only when you tap Done or Won’t do (`period`, `notes`, `completed_on`).
- **Last done** in UI: latest completion per `task_id` where `status = done`.

---

## Data model (Google Sheet — two tabs)

The sheet does **not** recur anything. **Recurrence lives in app code** (which templates apply to which month).

| Tab | Role |
|-----|------|
| **templates** | **One row per task, forever** — name, cadence, due month/day, area, active, … |
| **completions** | **Sparse** — one row only when you act: Done or Won’t do for a given `period` (`YYYY-MM`) |

**Pending / overdue are computed**, not stored as monthly instance rows.

**templates columns (minimum):** `task_id`, `name`, `cadence`, `due_month`, `due_day`, `area`, `active` (+ `gcal_series_id` in **v2**)

**completions columns (minimum):** `completion_id`, `task_id`, `period` (`YYYY-MM`), `status` (`done` / `wont_do`), `completed_on`, `notes` (+ `gcal_instance_id` in **v2**)

### How v1 builds the monthly list

For selected month *M*:

1. Select applicable **templates** (monthly always; annual when `due_month` matches *M*).
2. Load **completions** for period *M* (and earlier periods if needed for carry-over).
3. For each task:
   - **Done / Won’t do in *M*** → hidden or muted.
   - **No terminal completion for *M*** → **pending** for this month.
   - **No terminal completion for a prior required period** while viewing *M* → **overdue** (red).

### Month rollover (v1)

No defer rows are created at month end. When *M+1* opens, tasks that still lack Done/Won’t do for the period(s) they owed work in show as **overdue** until you act in the new month (implicit carry).

### Recurrence elsewhere

**v2 Google Calendar** owns native RRULE + phone reminders. The sheet stays templates + completions.

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
| 2026-11-17 | Data model: templates + sparse completions; pending computed in app |