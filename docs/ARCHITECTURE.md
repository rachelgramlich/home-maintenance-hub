# Architecture decision (current)

**Chosen direction:** Small **Python / Streamlit** repo developed in **Cursor**, **hidden Google Sheet** as data store, **Google Calendar** for recurrence and phone reminders. **Notion not required.**

**Rejected for v1:** Apps Script–first (hard for cloud agents to build/test end-to-end), paid apps, Zapier/Make, calendar-only workflow.

---

## What “last time I did X” means (product)

You want **lookup**, not a buried audit log:

- On each task (week view or task detail): **Last completed:** date, optional **notes**, optional **vendor/cost** later.
- Implemented by:
  - **`instances` sheet:** one row per task per period; when status → Done, set `completed_on` and `notes`.
  - **`last_done` in UI:** query latest instance per `task_id` where `status = Done` (or `Won't do` if you want that visible — default: Done only).

No separate “query vs save” choice — **saving each completion with notes automatically enables “last time”** in the app.

---

## Data model (Google Sheet — three tabs)

| Tab | Role |
|-----|------|
| **templates** | Stable task definitions + `gcal_series_id` |
| **instances** | Per-period state (pending/done/won’t do/defer), `due_date`, `completed_on`, **notes** |
| **history** (optional) | Append-only copy on action for extra safety; can skip if instances are never hard-deleted |

**templates columns (minimum):** `task_id`, `name`, `cadence`, `due_month`, `due_day`, `area`, `active`, `gcal_series_id`, `default_notes`

**instances columns (minimum):** `instance_id`, `task_id`, `period_key`, `status`, `due_date`, `carried_over`, `completed_on`, `notes`, `gcal_instance_id`

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

## One-time manual setup (unavoidable — Google APIs)

The agent can script everything **after** you complete this short checklist (~15–20 min, once):

1. **Google Cloud project** (or reuse household GCP): enable **Google Sheets API** + **Google Calendar API**.
2. **OAuth “Desktop” or “Web” client** for your Google account (same pattern as grocery-wizard Google auth if reused).
3. **Run once locally:** `just google-auth` (or similar) → stores **refresh token** in `secrets.toml` (agent provides command).
4. **Dedicated calendar:** create “Home maintenance” (or agent creates via API on first run); copy `GCAL_CALENDAR_ID` into secrets.
5. **Sheet:** agent script `just init-sheet` creates the workbook in your Drive and writes `SHEET_ID` to secrets — **you only sign in when the auth command opens the browser**.

Optional later: Streamlit Community Cloud secrets (same TOML as grocery-wizard). Partner does **not** need any of this — calendar subscription only.

---

## Migration A → B

Not applicable if we **start** with Streamlit + Sheet. The earlier Apps Script path was an optional phase-1; we skip it to match Cursor-first delivery.

---

## Revision log

| Date | Change |
|------|--------|
| 2026-11-17 | Lock Streamlit + Sheet + GCal; per-task last-done + notes; Cursor-first |