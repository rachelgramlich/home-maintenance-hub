"""Submit in-app feedback as GitHub inbox issues."""

from __future__ import annotations

from home_maintenance_hub.config import Settings, get_settings
from home_maintenance_hub.integrations.feedback_github import create_feedback_issue

__all__ = ["submit_feedback"]


def submit_feedback(
    text: str,
    *,
    surface: str | None = None,
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    token = cfg.github_feedback_token
    repo = cfg.github_feedback_repository
    if not token or not repo:
        raise RuntimeError(
            "Feedback requires GITHUB_FEEDBACK_TOKEN and GITHUB_FEEDBACK_REPOSITORY "
            "(environment or repo-root secrets.toml)",
        )
    issue = create_feedback_issue(text, repository=repo, token=token, surface=surface)
    number = issue.get("number")
    if number is None:
        return "github"
    return f"github #{number}"
