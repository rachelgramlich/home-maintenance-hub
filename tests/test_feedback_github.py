"""GitHub feedback issue payload tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from home_maintenance_hub.integrations.feedback_github import (
    FEEDBACK_GITHUB_INBOX_LABEL,
    create_feedback_issue,
)


def test_create_feedback_issue_posts_inbox_label() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"number": 42, "html_url": "https://example.com/issues/42"}
    mock_response.text = ""
    mock_response.reason = "Created"

    with patch(
        "home_maintenance_hub.integrations.feedback_github.requests.post", return_value=mock_response
    ) as post:
        result = create_feedback_issue(
            "  Filter chips look great  ",
            repository="rachelgramlich/home-maintenance-hub",
            token="github_pat_test",
            surface="monthly",
            timestamp="2026-11-20T12:00:00+00:00",
        )

    assert result["number"] == 42
    post.assert_called_once()
    _args, kwargs = post.call_args
    payload = kwargs["json"]
    assert FEEDBACK_GITHUB_INBOX_LABEL in payload["labels"]
    assert "monthly" in payload["body"]
    assert "Filter chips look great" in payload["body"]


def test_create_feedback_issue_rejects_bad_repo() -> None:
    with pytest.raises(ValueError, match="owner/repo"):
        create_feedback_issue("hi", repository="not-a-repo", token="t")
