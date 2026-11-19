# Maintenance Wizard — feature scope

**Product:** B & R Home Maintenance · **UI:** mockup C (monthly board + details drawer + Manage contractors)

## v1 — Monthly checklist (Notion-backed)

- **This month** view and month picker in sidebar (no calendar grid).
- Tasks for selected month from **`[MW] Tasks`** (xlsx-style: one row per task per month).
- **Done**, **Won’t do**, and **In progress**; completion **notes** on act only (stored in **`[MW] Completions`**).
- **Unmarked** work **carries** as **overdue** into later months (implicit; no Defer button).
- **Urgency:** overdue (red), optional due-soon (end of month window), open, in-progress badge.
- **Sort:** urgency bucket, then **priority** (High → Low), area, name.
- **Last done** + last completion note from completions log.
- Filter by **area** (and optional type / season).
- **Details drawer:** instructions, links, contractor (relation); view + **edit** template fields.
- **Manage contractors:** CRUD + “used by N tasks”; link from drawer.
- **Source of truth:** **Notion** (three databases). **Local JSON** for dev/CI only.
- One-time **migration** from Ocala xlsx `Home Maintenance` tab.
- Streamlit app; develop in Cursor.

**v1 does not include:** Google Calendar, proactive phone reminders, Google Sheet as live backend, calendar UI.

## v2 — Google Calendar

- Dedicated **Home maintenance** calendar; series from tasks.
- Sync on status changes; partner subscribes for reminders.
- OAuth/calendar setup at v2.

## v1.1 (optional)

- Weekly email digest (GitHub Action + Notion query).

## Revision log

| Date | Change |
|------|--------|
| 2026-11-17 | v1 month view, done/won’t do, implicit rollover |
| 2026-11-19 | In progress, contractors, drawer, Notion pivot |
| 2026-11-19 | Sheet backend removed from v1 scope |