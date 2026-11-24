# Naming standards (household Streamlit hubs)

| App | Display title | Repo | Package | Secrets file |
|-----|---------------|------|---------|--------------|
| Home maintenance | Home Maintenance Hub | `home-maintenance-hub` | `home_maintenance_hub` | repo-root `secrets.toml` |
| Grocery | Grocery Hub | `grocery-hub` | `grocery_hub` | repo-root `secrets.toml` |

**Environment variables:** unprefixed app keys in each repo's `secrets.toml` (or `.env`). Shared integrations use `NOTION_*`, `GITHUB_*`, and grocery-specific `NYT_*`. No `HOME_MAINTENANCE_*` or `GROCERY_*` app prefixes.

Reserve **wizard** only for multi-step UI flows inside an app, not product or repo names.
