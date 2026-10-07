"""Append-only audit trail of agent loop activity.

One JSON object per line (JSON Lines) at ``output/audit_trail.json``, appended
and never rewritten. A crash or a restart can only ever lose the single line
being written, never the history — so the trail survives across runs.

Each line records one agent turn: when it ran, who asked, the tool calls the
loop made (name, short args, short result), why the loop stopped, and a preview
of the reply. Customer PII returned by ``get_customer`` is redacted before it
is written.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
AUDIT_PATH = HERE.parent / "output" / "audit_trail.json"

#: Characters kept from any one args/result/message field. Keeps the trail
#: readable and stops a long prompt or product blob from bloating it.
MAX_FIELD = 200

# One process, but requests are served concurrently; serialise the appends so
# two turns finishing at once cannot interleave half-lines.
_LOCK = threading.Lock()


def short(value: object, limit: int = MAX_FIELD) -> str:
    """Collapse any value to a single trimmed, length-capped string."""
    text = value if isinstance(value, str) else json.dumps(value, default=str, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def record(
    *,
    user_id: int | None,
    message: str,
    tool_calls: list[dict],
    stop_reason: str,
    reply: str = "",
) -> None:
    """Append one turn to the trail. Best-effort: never raise into a chat turn."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "user": "anon" if user_id is None else f"user:{user_id}",
        "message": short(message, 160),
        "tool_calls": tool_calls,
        "stop_reason": stop_reason,
        "reply": short(reply, 160),
    }
    line = json.dumps(entry, ensure_ascii=False)
    try:
        with _LOCK:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with AUDIT_PATH.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
    except OSError:
        # A full disk should slow the shop, not break the chat.
        pass
