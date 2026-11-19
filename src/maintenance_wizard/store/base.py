from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from maintenance_wizard.models import Completion, CompletionStatus, Contractor, Template


class TaskStore(ABC):
    @abstractmethod
    def list_templates(self) -> list[Template]:
        raise NotImplementedError

    @abstractmethod
    def list_completions(self) -> list[Completion]:
        raise NotImplementedError

    @abstractmethod
    def upsert_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date | None,
        notes: str,
    ) -> Completion:
        raise NotImplementedError

    def add_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date,
        notes: str,
    ) -> Completion:
        return self.upsert_completion(task_id, period, status, completed_on, notes)

    def list_contractors(self, *, active_only: bool = True) -> list[Contractor]:
        return []

    def upsert_contractor(self, contractor: Contractor) -> Contractor:
        raise NotImplementedError

    def update_task(self, template: Template) -> Template:
        raise NotImplementedError

    def get_contractor(self, contractor_id: str) -> Contractor | None:
        for row in self.list_contractors(active_only=False):
            if row.contractor_id == contractor_id:
                return row
        return None
