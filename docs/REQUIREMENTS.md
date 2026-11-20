# Household recurring tasks — requirements & specification

> **Scope note (2026-11):** Shipped v1 is documented in [FEATURES.md](./FEATURES.md) and [ARCHITECTURE.md](./ARCHITECTURE.md). **Production data** is **Notion** (three databases) with **local JSON** for dev/CI only. Google Sheet is a **one-time migration source**, not a live backend. Sections below retain historical user stories where still relevant; defer to ARCHITECTURE when they conflict.

**Status:** Historical requirements + open product ideas  
**Product:** Streamlit **monthly maintenance board** on Notion (task catalog, completions, contractors)  
**Repo:** `maintenance-wizard`

---

## 1. Problem statement

Household maintenance and recurring chores were spread across spreadsheets and legacy Notion pages. v1 delivers a single **monthly board** in Streamlit backed by Notion: overdue carry-over, completion history, contractors, and a details drawer for rich metadata. Optional proactive reminders remain a later phase.

---

## 2. Goals

| ID | Goal |
|----|------|
| G1 | **Monthly board** (primary v1) for recurring tasks (monthly and annual cadences). |
| G2 | **Notion** = task catalog, completion history, and contractors (single write path in prod). |
| G3 | **Clear urgency** in the UI: overdue (red), open, completed hidden by default. No day-level “due soon” window. |
| G4 | **Carry-over:** unfinished tasks from prior periods surface as overdue until resolved (done, won’t do, or defer). |
| G5 | **Migrate** legacy xlsx/Sheet export into Notion (`just migrate-xlsx`); Sheet not used after cutover. |
| G6 | **Household deploy** on Streamlit Community Cloud + optional Google OIDC allowlist (see DEPLOYMENT.md). |

---

## 3. Non-goals (v1)

- Multi-household / multi-tenant SaaS.
- Complex project management (subtasks, dependencies, time tracking).
- Replacing Notion for free-form notes (app complements Notion).
- Native mobile app (responsive web is enough).
- Automatic vendor scheduling or cost analytics (optional fields only).
- Live Google Sheet backend or bidirectional Sheet sync (Notion wins after migration).

---

## 4. Users & context

- **Primary user:** Household member managing home maintenance (you).
- **Secondary:** Partner (same allowlist if deployed to Cloud).
- **Usage pattern:** Short sessions (5–10 min) at month start or when a reminder fires; occasional mid-month checkoffs.
- **Existing data:**
  - Deprecated Notion DB: **Maintenance Tasks** (61 templates) + **Maintenance Completions** (log without period/status).
  - Legacy Sheet/xlsx: one-time import only (see `scripts/migrate_xlsx.py`).

---

## 5. User stories

### Monthly workflow

| ID | Story | Acceptance hint |
|----|-------|-------------------|
| US1 | As a user, I open the app and see **this month’s** tasks grouped by urgency. | Default month = calendar month in user timezone. |
| US2 | As a user, I mark a task **Done** and it leaves the active list with a completion date. | Notion updated; UI refreshes. |
| US3 | As a user, I mark **Won’t do** for this period only. | Does not carry over; archived for that period. |
| US4 | As a user, I **Defer to next month** so the task appears next period, not as overdue today. | Status = Deferred; next period gets pending row. |
| US5 | As a user, I see **overdue** items from missed prior months in red at the top. | Carried-over flag + copy explains origin period. |
| US6 | As a user, I filter or group by **Area** (HVAC, Exterior, …). | Matches catalog metadata. |
| US7 | As a user, I switch to **another month** to review history or catch up. | Read-only past months allowed; actions only where policy allows. |

### Administration

| ID | Story |
|----|-------|
| US8 | As a user, I add/edit task **templates** in Notion (or a simple in-app form later). |
| US9 | As a user, I run a **one-time migration** from Google Sheet into Notion catalog. |

### Reminders (optional v1 / v1.1)

| ID | Story |
|----|-------|
| US10 | As a user, I get notified when tasks are **due or overdue** without opening the app. |

---

## 6. Functional requirements

### 6.1 Task catalog (templates)

Each template row describes a **recurring definition**, not a single month’s work.

| Req ID | Requirement |
|--------|-------------|
| FR-C1 | **Task** title (required). |
| FR-C2 | **Cadence:** `Monthly` or `Annual`. |
| FR-C3 | **Annual:** **Due month** (required for annual); optional **Due day** (1–28 recommended default 1 if blank). |
| FR-C4 | **Monthly:** due every calendar month; optional **Due day** (default: last day of month or 1st — **decision needed**). |
| FR-C5 | Metadata: **Area**, **Type**, **Effort**, **Priority**, **Notes** (optional; align with existing Notion enums where possible). |
| FR-C6 | **Active** checkbox; inactive templates do not spawn new period rows. |
| FR-C7 | Optional **Assignees** (person) for display only in v1. |

### 6.2 Period records (instances)

One row per **(template, period)** when the task is in play for that period.

| Req ID | Requirement |
|--------|-------------|
| FR-P1 | **Period key:** `YYYY-MM` for monthly tasks; for annual, `YYYY` or `YYYY-MM` per due rule (**decision needed**). |
| FR-P2 | **Status:** `Pending`, `Done`, `Won't do`, `Deferred`. |
| FR-P3 | **Due date** (date): computed when row is created (for sorting and reminders). |
| FR-P4 | **Carried over** (checkbox): true when created because a prior period was unresolved. |
| FR-P5 | **Completed on** (date): set when status → Done. |
| FR-P6 | **Relation** to catalog template (required). |
| FR-P7 | Rows are **lazy-created** when viewing a month (no batch job required for core UX). |

### 6.3 Scheduling & urgency rules

| Req ID | Rule |
|--------|------|
| FR-S1 | **Overdue (red):** Period ended (or due date passed — **decision needed**) AND status still `Pending`, OR carried-over row from earlier period still `Pending`. |
| FR-S2 | **Open:** `Pending` for the view month. Stays open for the whole month; there is no due-soon day window. |
| FR-S3 | **Deferred:** Current period row → `Deferred`; create/activate **next** period row as `Pending` (not overdue until that period’s rules say so). |
| FR-S4 | **Won't do:** Terminal for that period; no carry-over. |
| FR-S5 | **Done:** Terminal for that period; optional append to **completion log** for history (merge with or replace legacy Completions DB — **decision needed**). |
| FR-S6 | At month boundary, unresolved **Pending** rows generate **carried over** pending rows in the new month (or mark original overdue — **decision needed** for single vs duplicate rows). |

### 6.4 UI (Streamlit)

| Req ID | Requirement |
|--------|-------------|
| FR-U1 | Sidebar: month picker, filters (Area, cadence), toggle “Show completed”. |
| FR-U2 | Main: **Overdue**, then open tasks for the month (order fixed). |
| FR-U3 | Each task row: title, area, effort, badges (overdue). |
| FR-U4 | Actions: Done, Won’t do, Defer (confirm on defer optional). |
| FR-U5 | Empty states: no tasks, all complete, Notion misconfigured. |
| FR-U6 | Link to Notion page for power users (optional). |

### 6.5 Configuration & secrets

| Req ID | Requirement |
|--------|-------------|
| FR-X1 | Env: `NOTION_API_KEY`, `NOTION_TASK_CATALOG_DATABASE_ID`, `NOTION_PERIOD_RECORDS_DATABASE_ID`. |
| FR-X2 | Timezone default `America/New_York`. No due-soon days setting. |
| FR-X3 | Local dev without auth; Cloud deploy with Google allowlist (parity with grocery-wizard). |

### 6.6 Migration

| Req ID | Requirement |
|--------|-------------|
| FR-M1 | Import from **CSV export** of Google Sheet (v1 path; no Google OAuth required). |
| FR-M2 | Column mapping documented in `docs/migration-mapping.md` after sheet review. |
| FR-M3 | `--dry-run` reports creates/updates/skips. |
| FR-M4 | Optional import from deprecated Notion catalog (61 rows). |

---

## 7. Data model (Notion)

Two databases (production); optional `[HT CI]` copies for testing.

```mermaid
erDiagram
  TaskCatalog ||--o{ PeriodRecord : spawns
  TaskCatalog {
    string Task
    string Cadence
    string DueMonth
    int DueDay
    string Area
    bool Active
  }
  PeriodRecord {
    string Period
    string Status
    date DueDate
    bool CarriedOver
    date CompletedOn
  }
```

**Legacy:** `Maintenance Completions` may remain as a read-only archive or be folded into Period records + status Done (**decision needed**).

---

## 8. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR1 | Notion API errors shown clearly; no silent data loss. |
| NFR2 | Idempotent migration (re-run safe on title+area key). |
| NFR3 | Unit tests for scheduling/carry-over without live Notion. |
| NFR4 | Python 3.12, `uv`/`just`, ruff/pytest (lightweight vs grocery-wizard). |
| NFR5 | Personal data never committed to git. |

---

## 9. Reminders — product requirements

| Req ID | Requirement | Priority |
|--------|-------------|----------|
| REM1 | User can receive **at least one** proactive nudge per week or per due task. | Should (v1.1) |
| REM2 | Reminders must respect **Done / Won’t do / Deferred** (no spam). | Must |
| REM3 | Overdue tasks should **re-notify** on a bounded cadence (e.g. weekly, not hourly). | Should |
| REM4 | Content includes task name, due date, link to app or Notion. | Should |

---

## 10. Reminders — feasibility (technical)

Streamlit **does not run in the background**. When the browser tab is closed, the app cannot send notifications. Reminders require **an external scheduler** or **Notion’s notification system**.

### Option A: Notion-native reminders

**How it works:** Set `Due date` on period rows (or Notion reminders on that property). Users with Notion mobile/desktop get OS notifications when Notion fires reminders.

| | |
|--|--|
| **Feasibility** | High — no extra infra if you already use Notion on your phone. |
| **Pros** | Zero email API; works offline of Streamlit; partner can subscribe in Notion. |
| **Cons** | Easy to get noisy; per-row setup if not automated; reminder UX is Notion’s, not custom; must keep Due date accurate when deferring. |
| **Engineering** | App writes `Due date` on lazy row creation; optional script to bulk-set Notion reminder offset. |
| **Fit for v1** | **Best low-effort add-on** alongside in-app red/orange. |

### Option B: Scheduled job (GitHub Actions cron)

**How it works:** Daily workflow runs a Python script: query Notion → filter pending/overdue → send digest email (SendGrid, Resend, Amazon SES) or post to Slack webhook.

| | |
|--|--|
| **Feasibility** | High — same pattern as grocery-wizard’s Notion CI workflows; secrets in GitHub. |
| **Pros** | One **weekly digest** email (“3 overdue, 2 due this week”); full control of copy and cadence. |
| **Cons** | Requires email provider account + API key maintenance; GitHub Actions minute usage; not true “push at 9am on due day” unless you tune cron. |
| **Engineering** | ~1 workflow + `scripts/send_reminders.py` + dedupe state (e.g. “last_reminded_at” on row or KV in repo). |
| **Fit for v1** | **Best for email digests** if you want reminders outside Notion. |

### Option C: Slack

**How it works:** Cron or GitHub Action posts to a private channel or DM via Slack incoming webhook / bot token.

| | |
|--|--|
| **Feasibility** | High if you already use Slack daily; Medium if not. |
| **Pros** | Good for household shared channel; links clickable. |
| **Cons** | Another integration to secure and rotate. |
| **Fit** | Good **alternative to email** for your household. |

### Option D: Google Calendar (dedicated calendar) — **preferred for recurrence**

**How it works:** One calendar (e.g. “Home maintenance”). Each **template** maps to a **recurring GCal event** (monthly/annual RRULE). A sync job creates/updates series from the catalog; the app reflects **this week’s instances**. Phone reminders = native Google Calendar notifications.

| | |
|--|--|
| **Feasibility** | **High** for annual + monthly recurrence; **Medium** for Done/Defer/Won’t do (instance exceptions). |
| **Pros** | Annual tasks “just work”; partner subscribes to calendar; reminders you already use; hide calendar without losing catalog. |
| **Cons** | OAuth + sync code; must not two-way edit series blindly; completing one occurrence = Calendar **exception** API; overdue carry-over may need **extra one-off events** or Streamlit-only overdue section. |
| **Engineering** | `GCAL_CALENDAR_ID`, stored `gcal_event_id` / `gcal_series_id` on catalog row; `scripts/sync_gcal.py` + call from app on Done/Defer. |
| **Fit** | **Best primary reminder path** if Notion recurrence feels wrong. |

**Sync direction (recommended):** **Notion catalog → GCal** (one-way for series definition). **Completion state → Notion** (and optionally patch GCal instance: cancel occurrence, move date, or prefix title `[done]`). Treat **editing RRULE in GCal** as advanced/ discouraged unless we add two-way merge later.

See **§14 Architecture: weekly list + Google Calendar** for the full split-brain design.

### Option E: Third-party push (ntfy, Pushover, Twilio SMS)

| | |
|--|--|
| **Feasibility** | Medium — simple HTTP from cron; extra app on phone. |
| **Fit** | Nice if you want phone push without email; small scripts. |

### Recommended phasing (revised — calendar-first)

1. **v1:** Streamlit **This week** list + overdue (red/orange); Notion catalog + **period/completion** rows (lightweight).
2. **v1.1:** **GCal sync** on dedicated calendar — recurring series for all active templates; default alerts on events.
3. **v1.2 (optional):** Weekly **email digest** still fine as a “backup nudge” if you want inbox in addition to GCal; deprioritize Notion-native reminders.

```mermaid
flowchart LR
  subgraph v1 [v1 In app]
    UI[Streamlit badges]
  end
  subgraph v1a [v1.0.1 Low effort]
    N[Notion Due date reminders]
  end
  subgraph v11 [v1.1 Proactive]
    Cron[GitHub Actions daily]
    Cron --> Email[Email digest]
    Cron --> Slack[Slack message]
  end
  Notion[(Notion Period records)]
  Notion --> UI
  Notion --> N
  Notion --> Cron
```

---

## 14. Architecture: weekly list + Google Calendar (proposed)

### Why Notion struggles with annual recurrence

Notion databases are **rows**, not **recurrence engines**. An annual “service furnace in October” is naturally a **repeating calendar event** (`FREQ=YEARLY;BYMONTH=10`). Modeling that in Notion means either (a) generating new rows every year in a batch job, or (b) keeping a static catalog and simulating instances in app code—doable, but you rebuild what Google Calendar already provides, and **reminders** on Notion dates are easy to get wrong after defer/skip.

**Conclusion:** Use Notion for **what** the tasks are (sheet metadata, notes, history, completion audit). Use **GCal** for **when** they happen and **nagging your phone**.

### Recommended split

```mermaid
flowchart TB
  subgraph truth [Sources of truth]
    N[Notion catalog + completions]
    G[Google Calendar Home Maint]
  end
  subgraph app [Streamlit]
    W[This week list]
    A[Done / Wont do / Defer]
  end
  subgraph sync [Sync job]
    S[sync_gcal.py]
  end
  N --> W
  G --> W
  A --> N
  A --> S
  N --> S
  S --> G
```

| Concern | Owner |
|---------|--------|
| Task title, Area, Type, Effort, Notes, Active | Notion catalog |
| “Did we do it for 2025?” / Won’t do / Defer audit | Notion period or completion rows |
| RRULE: monthly, annual, due day | **Google Calendar event series** |
| Phone/email push before due | **GCal event reminders** |
| Overdue from missed weeks | Streamlit computes + optional **one-off GCal events** or digest only |
| Weekly review UI | Streamlit sorts by urgency |

### Weekly list as primary UI

Aligns with how you actually work: open app Sunday (or when GCal nudges), see **this week + overdue**, batch checkoffs. Month view becomes secondary (planning / annual preview).

**Week boundaries:** ISO week or “Sunday–Saturday” in `America/New_York` (**decision**).

### Google Calendar sync — how it would work

1. **One-time:** Create empty calendar “Home maintenance” (or use existing). OAuth once (same Google account as Streamlit auth is fine).
2. **Per catalog template:** Upsert a **recurring event** with:
   - Title: task name (optionally prefix Area)
   - Description: link to Notion page + app URL + `template_id`
   - RRULE from Cadence + due month/day
   - Default reminders: e.g. 1 week + 1 day (configurable per priority)
   - Store `gcal_recurring_event_id` on Notion catalog row
3. **Each week open in Streamlit:** Fetch **instances** in `[week_start, week_end]` via Calendar API `events.list` (expand recurring).
4. **Done:** Write Notion completion; call API to **mark this instance**—typically delete occurrence, create transparency “completed” exception, or set `extendedProperties` so sync does not resurrect it.
5. **Defer:** Move **this instance** to next week (`events.patch` on instance id); log Defer in Notion.
6. **Won’t do (this period):** `events.insert` with `transparency: transparent` or delete instance + Notion terminal status so resync skips until next recurrence.

**Re-sync policy:** Nightly or weekly GitHub Action reconciles Notion catalog → GCal series (new tasks, title changes, inactive templates delete series). Does **not** delete human-moved instances without rules.

### What calendars do *not* solve alone

- Rich filtering (Area, Effort) — keep in Streamlit from Notion metadata joined by `template_id` in event description.
- “Carried overdue since March” narrative — app logic + Notion; GCal might show only next instance unless we add a **separate overdue event**.
- Editing task library at scale — still nicer in Notion or sheet import.

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Partner edits event in GCal | v1: treat GCal as reminder layer only; completion only in app. v2: read instance changes cautiously. |
| OAuth token expiry | Refresh token in Streamlit secrets / GH secrets; `just gcal-auth` helper |
| Two calendars duplicate reminders | Single dedicated calendar; mute other lists |
| Annual task “skip 2026” | Won’t do writes EXDATE or deletes one instance; document pattern |

### Feasibility verdict

| Piece | Verdict |
|-------|---------|
| Dedicated GCal + annual RRULE | **Highly feasible** — this is the right tool. |
| Weekly Streamlit list from GCal instances | **Feasible** — join to Notion for metadata. |
| Full bidirectional Notion↔GCal for state | **Hard** — avoid; one-way series + app-driven instance patches. |
| Notion-only annual recurrence | **Possible but poor UX** — not recommended if GCal is acceptable. |

---

## 11. Open decisions (need your input)

Answer these to freeze the spec for implementation.

### Product

1. **Default monthly due day:** 1st of month, last day, or per-task from sheet?
2. **Overdue definition:** Due date passed, or “previous calendar month ended with no terminal status”?
3. **Carry-over model:** One row per period (new month = new row + carried flag) vs single row that moves period key?
4. **Annual tasks:** Show only in due month, or visible all year with orange in due month?
5. **Completion history:** Keep separate Completions log or only Period records?

### Data / migration

6. **Google Sheet:** Share column headers or CSV sample (or URL with export instructions).
7. **Source of truth after migration:** Sheet retired or kept as backup only?
8. **Reuse deprecated Notion catalog** as-is vs clean rename to `[HT] Task catalog`?

### Reminders & calendar

9. **Confirm GCal-first:** Dedicated “Home maintenance” calendar with sync from app?
10. **GCal default alerts:** e.g. 7 days + 1 day before, or day-of only?
11. **Supplementary weekly email digest** in addition to GCal, or GCal only?
12. **Partner:** Subscribe to same GCal (read-only) — sufficient for their reminders?

### Deploy

13. **Repo name** and **Streamlit deploy** in v1 or local-only first?
14. **Timezone** for week/month boundaries: `America/New_York`?

---

## 12. Success metrics (informal)

- You open the app (or read digest) **at least monthly** and clear overdue within the month.
- Migration completes with **zero duplicate** templates and spot-check of 10 tasks.
- No reminder fires for tasks marked Done/Won’t do in the same period (REM2).

---

## 13. Revision log

| Date | Change |
|------|--------|
| 2026-11-17 | Initial draft from planning session + deprecated Notion schema review |
| 2026-11-17 | §14 weekly list + GCal split; deprioritize Notion for annual recurrence |