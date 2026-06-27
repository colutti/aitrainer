"""Tests for Pydantic AI tool quality helpers."""

import pytest
from pydantic_ai import ModelRetry

from src.services.ai_chat.deps import ChatAgentDeps
from src.services.ai_chat.models import ToolResult
from src.services.ai_chat.tools.base import run_tool, tool_result_preview_for_log
from src.services.ai_chat.tools.registry import (
    PlanOpsAction,
    PlanOpsRequest,
    TrainingOpsAction,
    TrainingOpsRequest,
    build_chat_tools,
    plan_ops,
    training_ops,
)


class DummyContext:
    """Minimal RunContext stand-in for unit tests."""

    def __init__(self):
        self.deps = ChatAgentDeps(
            user_email="test@test.com",
            database=object(),
            qdrant_client=None,
            profile=object(),
            trainer_profile=object(),
            runtime_context={},
            tool_audit=[],
        )


def test_run_tool_records_successful_tool_audit_entry():
    ctx = DummyContext()

    def operation():
        return ToolResult(
            tool_name="get_plan_status",
            status="ACTIVE_PLAN",
            message_for_ai="Plano ativo encontrado.",
        )

    result = run_tool(ctx, "get_plan_status", {"limit": 1}, operation)

    assert result.status == "ACTIVE_PLAN"
    assert len(ctx.deps.tool_audit) == 1
    assert ctx.deps.tool_audit[0].tool_name == "get_plan_status"
    assert ctx.deps.tool_audit[0].args_preview == {"limit": 1}
    assert ctx.deps.tool_audit[0].result == result


def test_run_tool_converts_unexpected_exception_to_structured_result():
    ctx = DummyContext()

    def operation():
        raise RuntimeError("database down")

    result = run_tool(ctx, "get_plan_status", {"secret": "hidden"}, operation)

    assert result.tool_name == "get_plan_status"
    assert result.status == "error"
    assert result.saved is False
    assert "erro interno" in result.message_for_ai.lower()
    assert ctx.deps.tool_audit[0].error_type == "RuntimeError"
    assert "secret" not in ctx.deps.tool_audit[0].args_preview


def test_run_tool_records_model_retry_and_reraises_for_llm_correction():
    ctx = DummyContext()

    def operation():
        raise ModelRetry("Use YYYY-MM-DD.")

    with pytest.raises(ModelRetry):
        run_tool(ctx, "save_workout", {"date": "27/06/2026"}, operation)

    audit = ctx.deps.tool_audit[0]
    assert audit.error_type == "ModelRetry"
    assert audit.result is not None
    assert audit.result.status == "validation_error"
    assert audit.result.retryable is True
    assert "YYYY-MM-DD" in audit.result.message_for_ai


def test_tool_result_preview_for_log_removes_raw_payload():
    result = ToolResult(
        tool_name="get_memories_raw",
        status="success",
        message_for_ai="Memorias carregadas.",
        payload={
            "items": [{"content": "sensitive memory", "token": "hidden"}],
            "total": 1,
        },
    )

    preview = tool_result_preview_for_log(result)

    assert preview["tool_name"] == "get_memories_raw"
    assert preview["status"] == "success"
    assert preview["payload_preview"] == "dict(keys=['items', 'total'])"
    assert "payload" not in preview
    assert "sensitive memory" not in str(preview)
    assert "hidden" not in str(preview)


def test_domain_tools_have_llm_facing_docstrings():
    for tool in build_chat_tools():
        assert tool.__doc__
        assert "Use" in tool.__doc__
        assert "Args:" in tool.__doc__


def test_domain_tool_missing_required_action_parameter_raises_model_retry():
    ctx = DummyContext()
    request = TrainingOpsRequest(
        action=TrainingOpsAction.SAVE_WORKOUT,
        workout_type="strength",
        exercises=None,
    )

    with pytest.raises(ModelRetry) as exc_info:
        training_ops(ctx, request)

    assert "exercises" in str(exc_info.value)
    assert "save_workout" in str(exc_info.value)


def test_plan_ops_returns_structured_validation_error_for_missing_payload():
    ctx = DummyContext()
    request = PlanOpsRequest(action=PlanOpsAction.UPDATE_SECTION, payload=None)

    result = plan_ops(ctx, request)

    assert isinstance(result, ToolResult)
    assert result.status == "validation_error"
    assert result.retryable is True
    assert "payload" in result.message_for_ai
