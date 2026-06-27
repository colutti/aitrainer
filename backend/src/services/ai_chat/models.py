"""Typed contracts for the Pydantic AI chat runtime."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class OperationStatus(StrEnum):
    """Backend-visible outcome class for one chat turn."""

    NO_ACTION = "no_action"
    READ_ONLY = "read_only"
    SAVED = "saved"
    BLOCKED = "blocked"
    FAILED = "failed"


ToolStatus = Literal[
    "success",
    "ACTIVE_PLAN",
    "NO_PLAN",
    "DISCOVERY_IN_PROGRESS",
    "discovery_updated",
    "review_recorded",
    "not_found",
    "validation_error",
    "blocked",
    "external_error",
    "error",
]


class ToolResult(BaseModel):
    """Structured result every AI-facing tool must return."""

    tool_name: str
    status: ToolStatus | str
    saved: bool = False
    material_change: bool = False
    message_for_ai: str
    validation_errors: list[dict] = Field(default_factory=list)
    changed_resources: list[str] = Field(default_factory=list)
    retryable: bool = False
    external_sync_failed: bool = False
    payload: dict | list | str | int | float | bool | None = None


class ToolAuditEntry(BaseModel):
    """Backend-captured audit event for a tool call."""

    tool_name: str
    args_preview: dict = Field(default_factory=dict)
    result: ToolResult | dict[str, Any] | None = None
    duration_ms: int = 0
    error_type: str | None = None


class CoachTurnOutput(BaseModel):
    """Final typed output returned by the agent for a user-visible turn."""

    public_message: str = Field(min_length=1)
    operation_status: OperationStatus
    material_change: bool = False
    required_followup: str | None = None


class ChatRunLog(BaseModel):
    """Technical run log persisted for observability."""

    flow: str = "pydantic_ai_chat"
    status: str
    error_type: str | None = None
    requested_model: str = "unknown"
    resolved_model: str | None = None
    resolved_provider: str | None = None
    service_tier: str | None = None
    tokens_input: int = 0
    tokens_output: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    usage_cost: float | None = None
    duration_ms: int = 0
    context_load_ms: int = 0
    agent_run_ms: int = 0
    time_to_first_token_ms: int | None = None
    internal_requests: int = 0
    tool_calls_count: int = 0
    selected_toolsets: list[str] = Field(default_factory=list)
    available_tool_names: list[str] = Field(default_factory=list)
    available_tools_count: int = 0
    tools_called: list[str] = Field(default_factory=list)
    tool_audit: list[dict[str, Any]] = Field(default_factory=list)
    message_chars: int = 0
    history_messages_count: int = 0
