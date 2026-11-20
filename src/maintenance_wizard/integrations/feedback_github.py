"""Create GitHub issues for in-app feedback."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import requests

FEEDBACK_GITHUB_INBOX_LABEL = "user-feedback-inbox"
MAX_FEEDBACK_BODY_CHARS = 4000
_GITHUB_API = "https://api.github.com"
_MW_FOOTER = "_Auto-filed from Maintenance Wizard Send feedback._"


def _issue_title(text: str) -> str:
    one_line = " ".join(text.split())
    prefix = "User feedback: "
    max_len = 80
    room = max_len - len(prefix)
    if len(one_line) <= room:
        return f"{prefix}{one_line}"
    return f"{prefix}{one_line[: room - 1].rstrip()}…"


def _issue_body(*, text: str, surface: str | None, timestamp: str) -> str:
    header = [f"**Submitted:** {timestamp}"]
    if surface:
        header.append(f"**Surface:** {surface}")
    footer = f"\n\n---\n{_MW_FOOTER}"
    cleaned = text.rstrip()
    body = "\n".join([*header, "", cleaned]) + footer
    if len(body) <= MAX_FEEDBACK_BODY_CHARS:
        return body
    room = MAX_FEEDBACK_BODY_CHARS - len("\n".join(header)) - len(footer) - 3
    trimmed = cleaned[: max(room, 64)].rstrip() + "…"
    return "\n".join([*header, "", trimmed]) + footer


def create_feedback_issue(
    text: str,
    *,
    repository: str,
    token: str,
    surface: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("feedback text must be non-empty after stripping")

    repo = repository.strip().strip("/")
    if repo.count("/") != 1:
        raise ValueError("GITHUB_FEEDBACK_REPOSITORY must be owner/repo")

    when = timestamp or datetime.now(tz=UTC).isoformat()
    payload = {
        "title": _issue_title(cleaned),
        "body": _issue_body(text=cleaned, surface=surface, timestamp=when),
        "labels": [FEEDBACK_GITHUB_INBOX_LABEL],
    }
    url = f"{_GITHUB_API}/repos/{repo}/issues"
    response = requests.post(
        url,
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        timeout=30,
    )
    if response.status_code >= 400:
        detail = response.text.strip() or response.reason
        raise RuntimeError(f"GitHub issue create failed ({response.status_code}): {detail}")
    return response.json()
