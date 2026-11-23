"""Contract tests for NotionTaskStore.update_task (no live Notion in CI)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from home_maintenance_hub.config import Settings, get_settings
from home_maintenance_hub.integrations.notion import client as nc
from home_maintenance_hub.models import TaskLink, Template
from home_maintenance_hub.store.notion import NotionTaskStore


def _notion_page_from_template(t: Template) -> dict:
    return {
        "id": t.task_id,
        "properties": {
            "Task": {"type": "title", "title": [{"plain_text": t.name}]},
            "Month #": {"type": "number", "number": t.due_month},
            "Area": {"type": "select", "select": {"name": t.area}},
            "Type": {"type": "select", "select": {"name": t.task_type}},
            "Effort": {"type": "select", "select": {"name": t.effort}},
            "Priority": {"type": "select", "select": {"name": t.priority}},
            "Instructions": {
                "type": "rich_text",
                "rich_text": [{"plain_text": t.instructions}],
            },
            "Links JSON": {"type": "rich_text", "rich_text": [{"plain_text": "[]"}]},
            "Active": {"type": "checkbox", "checkbox": t.active},
            "Contractor": {
                "type": "relation",
                "relation": [{"id": t.contractor_id}] if t.contractor_id else [],
            },
        },
    }


@pytest.fixture
def notion_settings(monkeypatch: pytest.MonkeyPatch) -> Settings:
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_STORE", "notion")
    monkeypatch.setenv("NOTION_API_KEY", "secret_test")
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_NOTION_TASKS_DS_ID", "tasks-ds")
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_NOTION_CONTRACTORS_DS_ID", "ctr-ds")
    monkeypatch.setenv("HOME_MAINTENANCE_HUB_NOTION_COMPLETIONS_DS_ID", "cmp-ds")
    get_settings.cache_clear()
    yield get_settings()
    get_settings.cache_clear()


def test_update_task_calls_notion_pages_update(notion_settings: Settings, monkeypatch) -> None:
    captured: dict = {}

    template = Template(
        task_id="page-abc",
        name="Test filter change",
        due_month=3,
        area="HVAC",
        task_type="Maintenance",
        effort="Low",
        priority="High",
        instructions="Replace filter",
        links=(TaskLink(label="Manual", url="https://example.com"),),
        contractor_id="ctr-99",
    )

    def fake_update(*, page_id: str, properties: dict) -> dict:
        captured["page_id"] = page_id
        captured["properties"] = properties
        return _notion_page_from_template(template)

    mock_client = MagicMock()
    mock_client.pages.update.side_effect = fake_update
    monkeypatch.setattr(nc, "make_client", lambda _key: mock_client)

    store = NotionTaskStore(notion_settings)
    updated = store.update_task(template)

    assert captured["page_id"] == "page-abc"
    props = captured["properties"]
    assert props["Task"]["title"][0]["text"]["content"] == "Test filter change"
    assert props["Instructions"]["rich_text"][0]["text"]["content"] == "Replace filter"
    assert props["Contractor"]["relation"] == [{"id": "ctr-99"}]
    assert updated.name == template.name
    assert updated.contractor_id == "ctr-99"


def test_update_task_clears_contractor_relation(notion_settings: Settings, monkeypatch) -> None:
    captured: dict = {}

    template = Template(
        task_id="page-xyz",
        name="Solo task",
        due_month=1,
        area="Electrical",
        contractor_id=None,
    )

    def fake_update(*, page_id: str, properties: dict) -> dict:
        captured["properties"] = properties
        return _notion_page_from_template(template)

    mock_client = MagicMock()
    mock_client.pages.update.side_effect = fake_update
    monkeypatch.setattr(nc, "make_client", lambda _key: mock_client)

    store = NotionTaskStore(notion_settings)
    store.update_task(template)

    assert captured["properties"]["Contractor"] == {"relation": []}
