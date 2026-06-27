"""Deterministic detection for same-turn plan execution approvals."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from src.api.models.chat_history import ChatHistory

_APPROVAL_EXACT = {
    "ok",
    "sim",
    "pode",
    "pode aplicar",
    "pode atualizar",
    "pode criar",
    "aplica",
    "aplicar",
    "confirmo",
    "confirmado",
    "manda",
    "fechado",
    "esta aprovado",
    "ta aprovado",
}
_APPROVAL_HINTS = (
    "pode aplicar",
    "pode atualizar",
    "pode criar",
    "ok pode",
    "sim pode",
    "confirmo",
    "esta aprovado",
    "ta aprovado",
)
_UPDATE_HINTS = (
    "atualizar",
    "alterar",
    "ajustar",
    "aplicar",
    "mudar",
    "trocar",
    "reduzir",
    "aumentar",
)
_CREATE_HINTS = (
    "criar",
    "montar",
    "gerar",
    "fechar",
)


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
    return re.sub(r"\s+", " ", ascii_text).strip()


def _history_text(recent_history: list[Any]) -> str:
    parts: list[str] = []
    for item in recent_history[-8:]:
        if isinstance(item, ChatHistory):
            parts.append(item.text)
            continue
        for part in getattr(item, "parts", []) or []:
            content = getattr(part, "content", None)
            if isinstance(content, str):
                parts.append(content)
    return "\n".join(parts)


def _is_explicit_approval(user_input: str) -> bool:
    normalized = _normalize_text(user_input)
    return normalized in _APPROVAL_EXACT or any(
        hint in normalized for hint in _APPROVAL_HINTS
    )


def _has_update_context(normalized_history: str) -> bool:
    return "plano" in normalized_history and any(
        hint in normalized_history for hint in _UPDATE_HINTS
    )


def _has_create_context(normalized_history: str) -> bool:
    return "plano" in normalized_history and any(
        hint in normalized_history for hint in _CREATE_HINTS
    )


def detect_plan_execution_requirement(
    *,
    user_input: str,
    recent_history: list[Any],
    runtime_context: dict,
) -> dict[str, Any] | None:
    """Return required plan tool context when the current turn is an approval."""
    if not _is_explicit_approval(user_input):
        return None

    normalized_history = _normalize_text(_history_text(recent_history))
    plan_context = runtime_context.get("plan", {}) or {}
    has_active_plan = bool(plan_context.get("has_active_plan"))
    discovery = plan_context.get("discovery") or {}
    missing_fields = discovery.get("missing_fields") or []

    if (has_active_plan or _has_update_context(normalized_history)) and _has_update_context(
        normalized_history
    ):
        return {
            "explicit_user_approval": True,
            "mode": "update_active_plan",
            "required_tool": "update_plan_section",
            "must_execute_now": True,
        }

    if not has_active_plan and not missing_fields and _has_create_context(normalized_history):
        return {
            "explicit_user_approval": True,
            "mode": "create_from_discovery",
            "required_tool": "create_plan_from_discovery",
            "must_execute_now": True,
        }

    return None
