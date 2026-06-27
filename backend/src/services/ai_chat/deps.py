"""Dependency object passed to Pydantic AI tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.services.ai_chat.models import ToolAuditEntry


@dataclass(slots=True)
class ChatAgentDeps:
    # pylint: disable=too-many-instance-attributes
    """Runtime dependencies available to every chat tool."""

    user_email: str
    database: Any
    qdrant_client: Any | None
    profile: Any
    trainer_profile: Any
    runtime_context: dict
    tool_audit: list[ToolAuditEntry] = field(default_factory=list)
    hevy_service: Any | None = None
