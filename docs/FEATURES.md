# Feature scope

## v1 — Monthly checklist

- **This month** view (month picker for other months).
- Tasks that apply to the selected month (monthly + annual due that month).
- **Done** or **Won’t do** only (optional notes on done).
- **Unmarked** at month end → **auto carries to next month** as overdue (no Defer button).
- **Urgency:** overdue (red), due soon (orange), normal.
- **Last done** date + notes per task (from **completions** log, not one row per month).
- Filter by **area** (and metadata on templates).
- **Hidden Google Sheet** backend + one-time import from your sheet / deprecated Notion.
- Streamlit app; develop in Cursor.

**v1 does not include:** Google Calendar sync, proactive phone reminders, partner-facing UI (partner unaffected until v2 calendar).

## v2 — Google Calendar

- Dedicated **Home maintenance** calendar.
- Recurring events from templates; sync on status changes.
- Partner can subscribe for reminders.
- OAuth/calendar setup added at v2.

## Revision log

| Date | Change |
|------|--------|
| 2026-11-17 | v1 month view, done/won’t do, implicit month rollover; GCal → v2 |
| 2026-11-17 | Sheet: templates + completions; pending/overdue computed in app |