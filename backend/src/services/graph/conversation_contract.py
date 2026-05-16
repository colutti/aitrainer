"""Cross-turn conversation state contract.

Defines enums for action status, pending-action kind, and helpers to
serialize/parse compact state snapshots persisted as SYSTEM messages
in chat history.

In the sequential graph model, every specialist node runs every turn.
The contract tracks continuity (pending actions), not routing (ownership).
"""

from __future__ import annotations

import json
import re
from enum import Enum


class ActionStatus(Enum):
    """Outcome of the action a node attempted."""

    EXECUTED = "executed"
    FAILED = "failed"
    NEEDS_USER_INPUT = "needs_user_input"
    NO_ACTION_NEEDED = "no_action_needed"


class PendingActionKind(Enum):
    """Category of the pending work."""

    PLAN_DISCOVERY = "plan_discovery"
    PLAN_REVIEW = "plan_review"
    DOMAIN_EXECUTION = "domain_execution"
    DOMAIN_ANALYSIS = "domain_analysis"
    NONE = "none"


PENDING_ACTION_PRIORITY: list[str] = [
    PendingActionKind.DOMAIN_EXECUTION.value,
    PendingActionKind.PLAN_DISCOVERY.value,
    PendingActionKind.PLAN_REVIEW.value,
    PendingActionKind.DOMAIN_ANALYSIS.value,
    PendingActionKind.NONE.value,
]

_SNAPSHOT_MARKER = "[GRAPH_STATE_V1]"
_SNAPSHOT_JSON_RE = re.compile(
    r"\[GRAPH_STATE_V1\]\s*(\{)",
    re.DOTALL,
)

_SUMMARY_MARKER = "[CONVERSATION_SUMMARY_V1]"


def _extract_json_at_position(text: str, start_pos: int) -> str | None:
    """Extract a complete JSON object from `text` starting at `start_pos`."""
    if start_pos >= len(text) or text[start_pos] != "{":
        return None
    depth = 0
    in_string = False
    escape_next = False
    for i in range(start_pos, len(text)):
        ch = text[i]
        if escape_next:
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start_pos : i + 1]
    return None


def build_snapshot(state_payload: dict) -> str:
    """Serialize a conversation state dict to a SYSTEM-suitable snapshot string."""
    compact = json.dumps(state_payload, ensure_ascii=True, sort_keys=True)
    return f"{_SNAPSHOT_MARKER} {compact}"


def parse_latest_snapshot(raw_system_messages: list[str]) -> dict | None:
    """Return the latest valid state snapshot from a list of SYSTEM-message strings.

    Iterates in reverse so the most recent valid snapshot wins.
    """
    for msg in reversed(raw_system_messages):
        for match in _SNAPSHOT_JSON_RE.finditer(msg):
            json_text = _extract_json_at_position(msg, match.start(1))
            if json_text is None:
                continue
            try:
                payload = json.loads(json_text)
                if isinstance(payload, dict):
                    return payload
            except json.JSONDecodeError:
                continue
    return None


def build_conversation_summary(summary_text: str) -> str:
    """Serialize a conversation summary to a SYSTEM-suitable string."""
    return f"{_SUMMARY_MARKER} {summary_text.strip()}"


def parse_latest_summary(raw_system_messages: list[str]) -> str | None:
    """Return the latest conversation summary from system messages, or None."""
    for msg in reversed(raw_system_messages):
        if _SUMMARY_MARKER in msg:
            idx = msg.index(_SUMMARY_MARKER)
            content = msg[idx + len(_SUMMARY_MARKER):].strip()
            if content:
                return content
    return None


def default_conversation_state() -> dict:
    """Return a safe empty conversation state."""
    return {
        "active_domain": "general",
        "pending_action": {
            "kind": PendingActionKind.NONE.value,
            "status": ActionStatus.NO_ACTION_NEEDED.value,
            "missing_slots": [],
        },
        "last_action_status": ActionStatus.NO_ACTION_NEEDED.value,
    }


def merge_pending_action_update(base: dict, update: dict | None) -> dict:
    """Merge a specialist pending-action update into the current state."""
    if not update or not isinstance(update, dict):
        return base
    pending = dict(base.get("pending_action", {}))
    for key in pending:
        if key in update and update[key] is not None:
            pending[key] = update[key]
    base["pending_action"] = pending
    return base


def resolve_pending_action(suggestions: dict[str, dict]) -> dict:
    """Pick the highest-priority pending_action from specialist suggestions.

    Each key is a node name and each value is the pending_action dict
    suggested by that node.  Returns the merged winning suggestion or
    a default no-action dict.
    """
    best_action: dict | None = None
    best_priority = len(PENDING_ACTION_PRIORITY)
    for suggestion in suggestions.values():
        kind = suggestion.get("kind", PendingActionKind.NONE.value)
        try:
            priority = PENDING_ACTION_PRIORITY.index(kind)
        except ValueError:
            priority = len(PENDING_ACTION_PRIORITY)
        if priority < best_priority:
            best_priority = priority
            best_action = suggestion
    if best_action is not None:
        return dict(best_action)
    return {
        "kind": PendingActionKind.NONE.value,
        "status": ActionStatus.NO_ACTION_NEEDED.value,
        "missing_slots": [],
    }
