"""Shared helpers for high-quality Pydantic AI tools."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic_ai import ModelRetry

from src.core.logs import logger
from src.services.ai_chat.models import ToolAuditEntry, ToolResult

T = TypeVar("T", bound=ToolResult)
_SENSITIVE_KEYS = {
    "api_key",
    "authorization",
    "base64",
    "password",
    "secret",
    "token",
}


def sanitize_tool_args(args: dict[str, Any]) -> dict[str, Any]:
    """Return a compact, non-sensitive args preview for logs."""
    sanitized: dict[str, Any] = {}
    for key, value in args.items():
        lowered = key.lower()
        if any(secret in lowered for secret in _SENSITIVE_KEYS):
            continue
        if isinstance(value, str) and len(value) > 240:
            sanitized[key] = f"{value[:240]}..."
        elif isinstance(value, (int, float, bool)) or value is None:
            sanitized[key] = value
        elif isinstance(value, (list, tuple)):
            sanitized[key] = f"{type(value).__name__}(len={len(value)})"
        elif isinstance(value, dict):
            sanitized[key] = {
                str(nested_key): nested_value
                for nested_key, nested_value in list(value.items())[:8]
                if not any(secret in str(nested_key).lower() for secret in _SENSITIVE_KEYS)
            }
        else:
            sanitized[key] = type(value).__name__
    return sanitized


def _payload_preview(payload: Any) -> str | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return f"dict(keys={list(payload.keys())[:8]})"
    if isinstance(payload, list):
        return f"list(len={len(payload)})"
    if isinstance(payload, str):
        return f"str(len={len(payload)})"
    return type(payload).__name__


def tool_result_preview_for_log(result: ToolResult) -> dict[str, Any]:
    """Return a compact, non-sensitive result preview for prompt logs."""
    preview: dict[str, Any] = {
        "tool_name": result.tool_name,
        "status": result.status,
        "saved": result.saved,
        "material_change": result.material_change,
        "retryable": result.retryable,
        "external_sync_failed": result.external_sync_failed,
    }
    if result.changed_resources:
        preview["changed_resources"] = result.changed_resources
    if result.validation_errors:
        preview["validation_errors_count"] = len(result.validation_errors)
    payload_preview = _payload_preview(result.payload)
    if payload_preview is not None:
        preview["payload_preview"] = payload_preview
    return preview


def audit_entry_preview_for_log(entry: ToolAuditEntry) -> dict[str, Any]:
    """Return a compact, non-sensitive audit entry for persisted run logs."""
    result = entry.result
    if isinstance(result, ToolResult):
        result_preview: dict[str, Any] | None = tool_result_preview_for_log(result)
    elif isinstance(result, dict):
        result_preview = result
    else:
        result_preview = None
    return {
        "tool_name": entry.tool_name,
        "args_preview": entry.args_preview,
        "result": result_preview,
        "duration_ms": entry.duration_ms,
        "error_type": entry.error_type,
    }


def run_tool(
    ctx: Any,
    tool_name: str,
    args: dict[str, Any],
    operation: Callable[[], T],
) -> T | ToolResult:
    """Run a tool with standardized audit, timing, and error conversion."""
    start = time.perf_counter()
    audit = ToolAuditEntry(tool_name=tool_name, args_preview=sanitize_tool_args(args))
    try:
        result = operation()
        audit.result = result
        return result
    except ModelRetry as exc:
        audit.error_type = "ModelRetry"
        audit.result = ToolResult(
            tool_name=tool_name,
            status="validation_error",
            saved=False,
            material_change=False,
            message_for_ai=str(exc),
            retryable=True,
            validation_errors=[{"msg": str(exc), "type": "model_retry"}],
        )
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("AI tool %s failed", tool_name)
        audit.error_type = type(exc).__name__
        result = ToolResult(
            tool_name=tool_name,
            status="error",
            saved=False,
            material_change=False,
            message_for_ai=(
                "A ferramenta encontrou um erro interno e nao salvou nenhuma mudanca."
            ),
        )
        audit.result = result
        return result
    finally:
        audit.duration_ms = int((time.perf_counter() - start) * 1000)
        deps = getattr(ctx, "deps", None)
        if deps is not None and hasattr(deps, "tool_audit"):
            deps.tool_audit.append(audit)


async def run_async_tool(
    ctx: Any,
    tool_name: str,
    args: dict[str, Any],
    operation: Callable[[], Awaitable[T]],
) -> T | ToolResult:
    """Run an async tool with standardized audit, timing, and error conversion."""
    start = time.perf_counter()
    audit = ToolAuditEntry(tool_name=tool_name, args_preview=sanitize_tool_args(args))
    try:
        result = await operation()
        audit.result = result
        return result
    except ModelRetry as exc:
        audit.error_type = "ModelRetry"
        audit.result = ToolResult(
            tool_name=tool_name,
            status="validation_error",
            saved=False,
            material_change=False,
            message_for_ai=str(exc),
            retryable=True,
            validation_errors=[{"msg": str(exc), "type": "model_retry"}],
        )
        raise
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("AI tool %s failed", tool_name)
        audit.error_type = type(exc).__name__
        result = ToolResult(
            tool_name=tool_name,
            status="error",
            saved=False,
            material_change=False,
            message_for_ai=(
                "A ferramenta encontrou um erro interno e nao salvou nenhuma mudanca."
            ),
        )
        audit.result = result
        return result
    finally:
        audit.duration_ms = int((time.perf_counter() - start) * 1000)
        deps = getattr(ctx, "deps", None)
        if deps is not None and hasattr(deps, "tool_audit"):
            deps.tool_audit.append(audit)
