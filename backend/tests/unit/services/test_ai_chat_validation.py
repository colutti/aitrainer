"""Tests for deterministic AI chat truth policy validation."""

from src.services.ai_chat.models import CoachTurnOutput, OperationStatus, ToolResult
from src.services.ai_chat.validation import validate_turn_output


def test_saved_output_requires_real_saved_tool_result():
    output = CoachTurnOutput(
        public_message="Plano atualizado com sucesso.",
        operation_status=OperationStatus.SAVED,
        material_change=True,
    )

    validated = validate_turn_output(
        output=output,
        tool_results=[],
        user_locale="pt-BR",
        required_tool=None,
    )

    assert validated.operation_status == OperationStatus.BLOCKED
    assert validated.material_change is False
    assert "Nao executei" in validated.public_message


def test_required_tool_must_be_called_after_explicit_approval():
    output = CoachTurnOutput(
        public_message="Posso atualizar.",
        operation_status=OperationStatus.NO_ACTION,
    )

    validated = validate_turn_output(
        output=output,
        tool_results=[],
        user_locale="pt-BR",
        required_tool="update_plan_section",
    )

    assert validated.operation_status == OperationStatus.BLOCKED
    assert "update_plan_section" in validated.public_message


def test_material_change_requires_material_tool_result():
    output = CoachTurnOutput(
        public_message="Revisao registrada.",
        operation_status=OperationStatus.SAVED,
        material_change=True,
    )
    tool_result = ToolResult(
        tool_name="record_plan_review",
        status="review_recorded",
        saved=True,
        material_change=False,
        message_for_ai="Revisao registrada, sem mudar plano ativo.",
    )

    validated = validate_turn_output(
        output=output,
        tool_results=[tool_result],
        user_locale="pt-BR",
        required_tool=None,
    )

    assert validated.operation_status == OperationStatus.SAVED
    assert validated.material_change is False
    assert "sem mudar o plano ativo" in validated.public_message
