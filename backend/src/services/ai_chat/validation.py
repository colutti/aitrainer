"""Deterministic validation for final agent output."""

from __future__ import annotations

from src.services.ai_chat.models import CoachTurnOutput, OperationStatus, ToolResult


def _blocked_message(user_locale: str | None, reason: str) -> str:
    if user_locale == "en-US":
        return f"I did not execute the requested change. Blocker: {reason}"
    if user_locale == "es-ES":
        return f"No ejecute el cambio solicitado. Bloqueo: {reason}"
    return f"Nao executei a mudanca solicitada. Bloqueio: {reason}"


def _no_material_change_message(user_locale: str | None) -> str:
    if user_locale == "en-US":
        return "The information was saved, but without changing the active plan materially."
    if user_locale == "es-ES":
        return "La informacion fue guardada, pero sin cambiar materialmente el plan activo."
    return "A informacao foi salva, mas sem mudar o plano ativo materialmente."


def validate_turn_output(
    *,
    output: CoachTurnOutput,
    tool_results: list[ToolResult],
    user_locale: str | None,
    required_tool: str | None,
) -> CoachTurnOutput:
    """Ensure the user-visible response matches real backend tool outcomes."""
    if required_tool and not any(result.tool_name == required_tool for result in tool_results):
        return CoachTurnOutput(
            public_message=_blocked_message(
                user_locale, f"este turno nao executou `{required_tool}`"
            ),
            operation_status=OperationStatus.BLOCKED,
            material_change=False,
        )

    successful_saved = any(result.saved for result in tool_results)
    material_change = any(result.material_change for result in tool_results)
    external_failure = next(
        (result for result in tool_results if result.external_sync_failed),
        None,
    )
    failed_required = next(
        (
            result
            for result in tool_results
            if required_tool and result.tool_name == required_tool and not result.saved
        ),
        None,
    )

    if external_failure:
        return CoachTurnOutput(
            public_message=_blocked_message(
                user_locale, external_failure.message_for_ai or "sync externo falhou"
            ),
            operation_status=OperationStatus.BLOCKED,
            material_change=False,
        )

    if failed_required:
        return CoachTurnOutput(
            public_message=_blocked_message(
                user_locale, failed_required.message_for_ai or failed_required.status
            ),
            operation_status=OperationStatus.BLOCKED,
            material_change=False,
        )

    if output.operation_status == OperationStatus.SAVED and not successful_saved:
        return CoachTurnOutput(
            public_message=_blocked_message(
                user_locale, "nenhuma ferramenta confirmou persistencia com saved=true"
            ),
            operation_status=OperationStatus.BLOCKED,
            material_change=False,
        )

    if output.material_change and not material_change:
        return CoachTurnOutput(
            public_message=_no_material_change_message(user_locale),
            operation_status=output.operation_status,
            material_change=False,
            required_followup=output.required_followup,
        )

    return output
