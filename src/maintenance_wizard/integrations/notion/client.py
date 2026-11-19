from __future__ import annotations

from typing import Any

from notion_client import Client

NOTION_VERSION = "2025-09-03"


def make_client(api_key: str) -> Client:
    return Client(auth=api_key, notion_version=NOTION_VERSION)


def paginate_data_source(client: Client, data_source_id: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        body: dict[str, Any] = {}
        if cursor:
            body["start_cursor"] = cursor
        page = client.request(
            path=f"data_sources/{data_source_id}/query",
            method="POST",
            body=body,
        )
        results.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")
    return results


def plain_text(prop: dict[str, Any] | None) -> str:
    if not prop:
        return ""
    if prop.get("type") == "title":
        parts = prop.get("title") or []
    elif prop.get("type") == "rich_text":
        parts = prop.get("rich_text") or []
    else:
        return ""
    return "".join(part.get("plain_text", "") for part in parts)


def select_name(prop: dict[str, Any] | None) -> str:
    if not prop or prop.get("type") != "select":
        return ""
    sel = prop.get("select")
    if not sel:
        return ""
    return str(sel.get("name", ""))


def checkbox_value(prop: dict[str, Any] | None) -> bool:
    if not prop or prop.get("type") != "checkbox":
        return False
    return bool(prop.get("checkbox"))


def number_value(prop: dict[str, Any] | None) -> float | None:
    if not prop or prop.get("type") != "number":
        return None
    return prop.get("number")


def date_start(prop: dict[str, Any] | None) -> str | None:
    if not prop or prop.get("type") != "date":
        return None
    d = prop.get("date")
    if not d:
        return None
    return d.get("start")


def relation_ids(prop: dict[str, Any] | None) -> list[str]:
    if not prop or prop.get("type") != "relation":
        return []
    return [str(r.get("id", "")) for r in prop.get("relation") or [] if r.get("id")]


def rich_text_value(text: str) -> dict[str, Any]:
    if not text:
        return {"rich_text": []}
    return {"rich_text": [{"type": "text", "text": {"content": text[:2000]}}]}


def title_value(text: str) -> dict[str, Any]:
    return {"title": [{"type": "text", "text": {"content": text[:2000]}}]}


def select_value(name: str) -> dict[str, Any]:
    if not name:
        return {"select": None}
    return {"select": {"name": name}}


def checkbox_prop(value: bool) -> dict[str, Any]:
    return {"checkbox": value}


def number_prop(value: float | int) -> dict[str, Any]:
    return {"number": float(value)}


def date_prop(iso_date: str) -> dict[str, Any]:
    return {"date": {"start": iso_date}}


def relation_prop(page_ids: list[str]) -> dict[str, Any]:
    return {"relation": [{"id": pid} for pid in page_ids]}
