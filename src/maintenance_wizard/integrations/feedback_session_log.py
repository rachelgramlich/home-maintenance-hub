"""Attach latest board session debug log to feedback bodies."""

from __future__ import annotations

import json
from typing import Any

_DEBUG_FENCE_OPEN = "```json\n"
_DEBUG_FENCE_CLOSE = "\n```"


def enrich_feedback_with_session_debug_log(
    text: str,
    *,
    debug_log: dict[str, Any] | None,
    notion_url: str | None = None,
) -> str:
    if debug_log is None and not notion_url:
        return text
    parts = [text.rstrip(), ""]
    if notion_url:
        parts.append(f"**Session debug log (Notion):** {notion_url}")
        parts.append("")
    if debug_log is not None:
        parts.append("**Session debug log (JSON):**")
        parts.append(_DEBUG_FENCE_OPEN + json.dumps(debug_log, indent=2) + _DEBUG_FENCE_CLOSE)
    return "\n".join(parts)
