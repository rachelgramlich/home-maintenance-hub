# Notion setup — Maintenance Wizard

Created **2026-11-19** in your workspace via Cursor Notion connection.

## Hub page

**[B & R Home Maintenance (Maintenance Wizard)](https://app.notion.com/p/41deab9e05398149bde2d52d4d86f912)**

Child databases live under this page.

## Databases

| Database | Notion URL | Data source ID (`collection://…`) |
|----------|------------|-------------------------------------|
| **[MW] Contractors** | https://app.notion.com/p/41deab9e0539814c9aaccbdaa47388e4 | `41deab9e-0539-81c9-b8c7-000b4652624d` |
| **[MW] Tasks** | https://app.notion.com/p/41deab9e0539818ba07befad106f90e2 | `41deab9e-0539-81e4-909b-000bf0fd4350` |
| **[MW] Completions** | https://app.notion.com/p/41deab9e0539819aba01e7938c59fdec | `41deab9e-0539-813a-8f1e-000bcecab247` |

Relations:

- **Tasks** ↔ **Contractors** (`Contractor` / `Tasks`)
- **Completions** ↔ **Tasks** (`Task` / `Completions`)

## App integration (you)

1. [Create a Notion integration](https://www.notion.so/my-integrations) (internal).
2. On the hub page, **⋯ → Connections → Add** your integration (grants all child DBs).
3. Copy the secret → `NOTION_API_KEY` in `.env` / Streamlit secrets.
4. Set data source IDs (see `.env.example`).

The databases created here are visible to **Cursor’s Notion MCP**; your **Streamlit** integration is a separate token with access to the same pages.

## Optional `[MW CI]` copies

For safe migration dry-runs, duplicate the three databases into a `[MW CI]` page and point a `notion` dev env at those IDs.

## Legacy

Do not import new work into **`__Deprecated_Home maintenance tasks`** (`collection://d7cb0608-b694-4103-b3ce-65af4fc82d3c`). Use **`[MW] Tasks`** after xlsx migration.