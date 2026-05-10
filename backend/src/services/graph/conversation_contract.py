"""Cross-turn conversation state contract.

Defines enums for interaction mode, primary owner, pending-action shape, and
helpers to serialize/parse compact state snapshots persisted as SYSTEM messages
in chat history.
"""

from __future__ import annotations

import json
import re
from enum import Enum


class InteractionMode(Enum):
    """What kind of conversation turn this is."""

    GENERAL = "general"
    DOMAIN_ANALYSIS = "domain_analysis"
    PLAN_DISCOVERY = "plan_discovery"
    PLAN_REVIEW = "plan_review"
    SLOT_ANSWER = "slot_answer"
    EXECUTION_REQUEST = "execution_request"
    CLARIFICATION = "clarification"


class PrimaryOwner(Enum):
    """Which node should lead the turn."""

    TRAINING_SPECIALIST = "training_specialist"
    NUTRITION_SPECIALIST = "nutrition_specialist"
    PLAN_SPECIALIST = "plan_specialist"
    COACH_REPLY = "coach_reply"


class ActionStatus(Enum):
    """Outcome of the action a node attempted."""

    EXECUTED = "executed"
    NEEDS_USER_INPUT = "needs_user_input"
    DEFERRED = "deferred"
    ESCALATE_TO_PLAN = "escalate_to_plan"
    NO_ACTION_NEEDED = "no_action_needed"


class PendingActionKind(Enum):
    """Category of the pending work."""

    PLAN_DISCOVERY = "plan_discovery"
    PLAN_REVIEW = "plan_review"
    DOMAIN_EXECUTION = "domain_execution"
    DOMAIN_ANALYSIS = "domain_analysis"
    NONE = "none"


_SNAPSHOT_MARKER = "[GRAPH_STATE_V1]"
_SNAPSHOT_JSON_RE = re.compile(
    r"\[GRAPH_STATE_V1\]\s*(\{)",
    re.DOTALL,
)


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


def default_conversation_state() -> dict:
    """Return a safe empty conversation state."""
    return {
        "active_domain": "general",
        "interaction_mode": InteractionMode.GENERAL.value,
        "primary_owner": PrimaryOwner.COACH_REPLY.value,
        "pending_action": {
            "kind": PendingActionKind.NONE.value,
            "status": ActionStatus.NO_ACTION_NEEDED.value,
            "missing_slots": [],
        },
        "last_action_status": ActionStatus.NO_ACTION_NEEDED.value,
    }


def merge_pending_action_update(base: dict, update: dict | None) -> dict:
    """Merge a router/specialist pending-action update into the current state."""
    if not update or not isinstance(update, dict):
        return base
    pending = dict(base.get("pending_action", {}))
    for key in pending:
        if key in update and update[key] is not None:
            pending[key] = update[key]
    base["pending_action"] = pending
    return base
