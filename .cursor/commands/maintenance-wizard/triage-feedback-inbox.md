---
name: triage-feedback-inbox
description: Triage GitHub user-feedback-inbox issues → draft backlog plan → promote after user approval
---

# Triage feedback inbox (GitHub → backlog)

**Scope: triage only.** List open issues labeled **`user-feedback-inbox`** (from Streamlit **Send feedback**), draft a promotion plan in chat (merge, split, rewrite, areas), then create or update real backlog issues **only after the user approves**. Do not run **`/work-on-issue`** in this turn unless the user asks separately.

**Related:** **`/create-issues-from-backlog`** is a short pointer to this command.

## Requires `gh`

Authenticate **`gh`** for `rachelgramlich/maintenance-wizard` when creating, closing, or labeling issues.

## Do not implement in this turn

- Do not open PRs, branches, or application code changes unless the user asks **after** backlog issues exist.
- Do not run **`/work-on-issue`** in this turn.

## Inbox source (GitHub)

| Item | Value |
| --- | --- |
| **List** | `gh issue list --label user-feedback-inbox --state open --json number,title,body,labels,createdAt,url` |
| **One issue** | `gh issue view <n> --json number,title,body,labels,comments,url` |
| **Search backlog dupes** | `gh issue list --label maintenance-wizard --state open --search "<keywords>" --limit 20` |

If the inbox is **empty**, say so and stop after suggesting a test submission via **`just ui`** (requires **`GITHUB_FEEDBACK_TOKEN`** in `.streamlit/secrets.toml` or env).

## Planning rules

Read **`AGENTS.md`** for **backlog label**, **bug label**, **area labels**, and issue body sections.

1. **Kind:** **`bug`** if broken behavior; otherwise **enhancement** → **`maintenance-wizard`** (+ **`mw-area-*`**).
2. **Area:** Map to **`mw-area-ui`**, **`mw-area-store`**, **`mw-area-domain`**, **`mw-area-notion`**, or **`mw-area-other`**.
3. **Merge / split / rewrite** per grocery-wizard triage conventions.
4. **Existing backlog:** Prefer updating an open **`maintenance-wizard`** issue instead of duplicating.

## Draft plan (required before promotion)

- Inbox issues reviewed
- Proposed backlog issues (title, kind, labels, mapping)
- Skipped / needs info
- Dupes of open backlog

Use template sections: **Description**, **Expected behavior & manual test hints**, **Area**, plus **Original feedback** from inbox bodies.

## Promotion phase (only after user approval)

1. Ensure label **`promoted`** exists (create if missing).
2. **`gh issue create`** or comment on existing backlog issues.
3. For each consumed inbox issue: link promoted items, remove **`user-feedback-inbox`**, add **`promoted`**, close unless user wants audit trail.
4. Summarize new backlog numbers and suggest **`/work-on-issue <n>`**.

## Your task

1. List open **`user-feedback-inbox`** issues.
2. Search for duplicate backlog items.
3. Post draft plan and **wait for approval**.
4. On approval, run promotion **`gh`** commands and summarize.