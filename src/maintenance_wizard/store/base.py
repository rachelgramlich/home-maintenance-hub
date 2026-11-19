from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from maintenance_wizard.models import Completion, CompletionStatus, Template


class TaskStore(ABC):
    @abstractmethod
    def list_templates(self) -> list[Template]:
        raise NotImplementedError

    @abstractmethod
    def list_completions(self) -> list[Completion]:
        raise NotImplementedError

    @abstractmethod
    def add_completion(
        self,
        task_id: str,
        period: str,
        status: CompletionStatus,
        completed_on: date,
        notes: str,
    ) -> Completion:
        raise NotImplementedError
