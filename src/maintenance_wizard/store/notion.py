from __future__ import annotations

from datetime import date
from typing import Any

from maintenance_wizard.config import Settings
from maintenance_wizard.domain.schedule import completion_page_title
from maintenance_wizard.integrations.notion import client as nc
from maintenance_wizard.integrations.notion.mappers import (
    page_to_completion,
    page_to_contractor,
    page_to_template,
)
from maintenance_wizard.models import (
    Completion,
    CompletionStatus,
    Contractor,
    Template,
    links_to_json,
)
from maintenance_wizard.store.base import TaskStore


class NotionTaskStore(TaskStore):
    def __init__(self, settings: Settings) -> None:
        if not settings.notion_api_key:
            msg = "Set NOTION_API_KEY for notion store"
            raise RuntimeError(msg)
        for name, value in (
            ("tasks", settings.notion_tasks_ds_id),
            ("contractors", settings.notion_contractors_ds_id),
            ("completions", settings.notion_completions_ds_id),
        ):
            if not value:
                msg = f"Set MAINTENANCE_WIZARD_NOTION_{name.upper()}_DS_ID"
                raise RuntimeError(msg)
        self._settings = settings
        self._client = nc.make_client(settings.notion_api_key)
        self._task_name_cache: dict[str, str] | None = None

    def _task_names_by_id(self) -> dict[str, str]:
        if self._task_name_cache is None:
            pages = nc.paginate_data_source(self._client, self._settings.notion_tasks_ds_id)
            self._task_name_cache = {
                page_to_template(p).task_id: page_to_template(p).name for p in pages
            }
        return self._task_name_cache

    def _task_name(self, task_id: str) -> str:
        return self._task_names_by_id().get(task_id, "Unknown task")

    def list_templates(self) -> list[Template]:
        pages = nc.paginate_data_source(self._client, self._settings.notion_tasks_ds_id)
        templates = [page_to_template(p) for p in pages]
        return [t for t in templates if t.active]

    def list_templates_all(self) -> list[Template]:
        pages = nc.paginate_data_source(self._client, self._settings.notion_tasks_ds_id)
        return [page_to_template(p) for p in pages]

    def list_completions(self) -> list[Completion]:
        pages = nc.paginate_data_source(self._client, self._settings.notion_completions_ds_id)
        return [page_to_completion(p) for p in pages]

    def list_contractors(self, *, active_only: bool = True) -> list[Contractor]:
        pages = nc.paginate_data_source(self._client, self._settings.notion_contractors_ds_id)
        contractors = [page_to_contractor(p) for p in pages]
        if active_only:
            contractors = [c for c in contractors if c.active]
        return contractors

    def _completion_index(self) -> dict[tuple[str, str], dict[str, Any]]:
        pages = nc.paginate_data_source(self._client, self._settings.notion_completions_ds_id)
        out: dict[tuple[str, str], dict[str, Any]] = {}
        for page in pages:
            comp = page_to_completion(page)
            if comp.task_id and comp.period:
                out[(comp.task_id, comp.period)] = page
        return out

    def upsert_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date | None,
        notes: str,
    ) -> Completion:
        index = self._completion_index()
        existing = index.get((task_id, period))
        title = completion_page_title(
            task_name=self._task_name(task_id),
            period=period,
            status=status,
        )
        props: dict[str, Any] = {
            "Name": nc.title_value(title),
            "Period": nc.rich_text_value(period),
            "Status": nc.select_value(status),
            "Notes": nc.rich_text_value(notes),
            "Task": nc.relation_prop([task_id]),
        }
        if completed_on:
            props["Completed on"] = nc.date_prop(completed_on.isoformat())

        if existing:
            page_id = str(existing["id"])
            updated = self._client.pages.update(page_id=page_id, properties=props)
        else:
            ds_id = self._settings.notion_completions_ds_id
            updated = self._client.pages.create(
                parent={"type": "data_source_id", "data_source_id": ds_id},
                properties=props,
            )
        return page_to_completion(updated)

    def update_task(self, template: Template) -> Template:
        props: dict[str, Any] = {
            "Task": nc.title_value(template.name),
            "Month #": nc.number_prop(template.due_month),
            "Area": nc.select_value(template.area),
            "Type": nc.select_value(template.task_type),
            "Effort": nc.select_value(template.effort),
            "Priority": nc.select_value(template.priority),
            "Instructions": nc.rich_text_value(template.instructions),
            "Links JSON": nc.rich_text_value(links_to_json(template.links)),
            "Active": nc.checkbox_prop(template.active),
        }
        if template.month_name:
            props["Month"] = nc.select_value(template.month_name)
        if template.season:
            props["Season"] = nc.select_value(template.season)
        if template.contractor_id:
            props["Contractor"] = nc.relation_prop([template.contractor_id])
        else:
            props["Contractor"] = {"relation": []}

        updated = self._client.pages.update(page_id=template.task_id, properties=props)
        self._task_name_cache = None
        return page_to_template(updated)

    def upsert_contractor(self, contractor: Contractor) -> Contractor:
        props: dict[str, Any] = {
            "Name": nc.title_value(contractor.name),
            "Trade": nc.select_value(contractor.trade),
            "Phone": nc.rich_text_value(contractor.phone),
            "Email": nc.rich_text_value(contractor.email),
            "Notes": nc.rich_text_value(contractor.notes),
            "Active": nc.checkbox_prop(contractor.active),
        }
        if contractor.website:
            props["Website"] = {"url": contractor.website}
        if contractor.contractor_id:
            updated = self._client.pages.update(
                page_id=contractor.contractor_id,
                properties=props,
            )
        else:
            updated = self._client.pages.create(
                parent={
                    "type": "data_source_id",
                    "data_source_id": self._settings.notion_contractors_ds_id,
                },
                properties=props,
            )
        return page_to_contractor(updated)
