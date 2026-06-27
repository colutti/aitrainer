"""Tool registry for the Pydantic AI chat agent."""
# pylint: disable=too-many-lines,too-many-arguments,too-many-positional-arguments,too-many-locals
# pylint: disable=too-many-return-statements
# pylint: disable=unused-argument

from __future__ import annotations

import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_ai import ModelRetry, RunContext
from pydantic_ai.toolsets import FunctionToolset

from src.api.models.plan import (
    PlanCreateInput,
    PlanDiscoveryUpdateInput,
    PlanReviewInput,
    PlanSectionUpdateInput,
)
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.ai_chat.deps import ChatAgentDeps
from src.services.ai_chat.models import ToolResult
from src.services.ai_chat.tools.base import run_async_tool, run_tool
from src.services.composition_tools import (
    create_get_composition_tool,
    create_save_composition_tool,
)
from src.services.event_tools import (
    create_create_event_tool,
    create_delete_event_tool,
    create_list_events_tool,
    create_update_event_tool,
)
from src.services.hevy_tools import (
    create_create_hevy_routine_tool,
    create_get_hevy_routine_detail_tool,
    create_list_hevy_routines_tool,
    create_replace_hevy_exercise_tool,
    create_search_hevy_exercises_tool,
    create_set_routine_rest_and_ranges_tool,
    create_trigger_hevy_import_tool,
    create_update_hevy_routine_tool,
)
from src.services.memory_tools import (
    create_delete_memories_batch_tool,
    create_delete_memory_tool,
    create_list_raw_memories_tool,
    create_save_memory_tool,
    create_search_memory_tool,
    create_update_memory_tool,
)
from src.services.metabolism_tools import (
    create_reset_tdee_tracking_tool,
    create_update_tdee_params_tool,
)
from src.services.nutrition_tools import (
    create_get_nutrition_tool,
    create_save_nutrition_tool,
    create_sync_nutrition_text_tool,
)
from src.services.plan_hevy_sync import HevySyncError, sync_training_with_hevy_if_needed
from src.services.plan_service import (
    apply_discovery_update,
    attach_review,
    build_plan_from_create_input,
    build_plan_view_model,
    build_progress_snapshot,
    build_review_record,
    merge_plan_section,
    missing_discovery_fields,
)
from src.services.plan_training_tools import create_get_plan_training_program_tool
from src.services.profile_tools import (
    create_get_user_goal_tool,
    create_update_user_goal_tool,
)
from src.services.raw_data_tools import (
    create_get_body_composition_raw_tool,
    create_get_events_raw_tool,
    create_get_goal_history_raw_tool,
    create_get_memories_raw_tool,
    create_get_nutrition_raw_tool,
    create_get_workouts_raw_tool,
)
from src.services.workout_tools import create_get_workouts_tool, create_save_workout_tool

MAX_AI_TOOLS_PER_TURN = 10


class PlanOpsAction(StrEnum):
    """Supported plan-domain operations."""

    GET_STATUS = "get_status"
    GET_PLAN = "get_plan"
    HELP = "help"
    GET_TRAINING_PROGRAM = "get_training_program"
    UPDATE_DISCOVERY = "update_discovery"
    CREATE_FROM_DISCOVERY = "create_from_discovery"
    UPDATE_SECTION = "update_section"
    RECORD_REVIEW = "record_review"


class PlanOpsRequest(BaseModel):
    """Typed request for `plan_ops`."""

    action: Literal[
        "get_status",
        "get_plan",
        "help",
        "get_training_program",
        "update_discovery",
        "create_from_discovery",
        "update_section",
        "record_review",
    ] = Field(description="The exact plan operation to execute.")
    payload: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Action-specific object. Required for update_discovery, "
            "create_from_discovery, update_section, and record_review."
        ),
    )
    output_format: Literal["text", "json"] = Field(
        default="text",
        description="Format for action=get_training_program.",
    )


class TrainingOpsAction(StrEnum):
    """Supported workout/training log operations."""

    SAVE_WORKOUT = "save_workout"
    GET_WORKOUTS = "get_workouts"


class WorkoutExerciseInput(BaseModel):
    """One exercise entry inside a completed workout log."""

    name: str = Field(description="Exercise name as provided by the user.")
    sets: int | None = Field(default=None, description="Number of completed sets.")
    reps: int | str | None = Field(
        default=None,
        description="Completed reps or rep range, preserving user wording when needed.",
    )
    weight: float | str | None = Field(
        default=None,
        description="Load used, including units when the user supplied them.",
    )
    notes: str | None = Field(default=None, description="Exercise-specific notes.")


class TrainingOpsRequest(BaseModel):
    """Typed request for `training_ops`."""

    action: Literal["save_workout", "get_workouts"] = Field(
        description="The exact training operation to execute."
    )
    workout_type: str | None = Field(
        default=None,
        description="Required for action=save_workout, for example strength or cardio.",
    )
    exercises: list[dict[str, Any]] | None = Field(
        default=None,
        description="Required for action=save_workout; completed exercises only.",
    )
    date: str | None = Field(default=None, description="Workout date in YYYY-MM-DD when known.")
    duration_minutes: int | None = Field(
        default=None,
        description="Workout duration in minutes when known.",
    )
    notes: str | None = Field(default=None, description="Workout-level notes.")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum recent workouts to read.")


class NutritionOpsAction(StrEnum):
    """Supported nutrition operations."""

    SAVE_DAILY_TOTALS = "save_daily_totals"
    GET_RECENT = "get_recent"
    SYNC_TEXT = "sync_text"


class NutritionOpsRequest(BaseModel):
    """Typed request for `nutrition_ops`."""

    action: Literal["save_daily_totals", "get_recent", "sync_text"] = Field(
        description="The exact nutrition operation to execute."
    )
    calories: int | float | str | None = Field(
        default=None,
        description="Required for action=save_daily_totals; consumed calories.",
    )
    protein_grams: float | str | None = Field(default=None, description="Consumed protein.")
    carbs_grams: float | str | None = Field(default=None, description="Consumed carbohydrates.")
    fat_grams: float | str | None = Field(default=None, description="Consumed fat.")
    fiber_grams: float | str | None = Field(default=None, description="Consumed fiber.")
    date: str | None = Field(default=None, description="Nutrition date in YYYY-MM-DD when known.")
    notes: str | None = Field(default=None, description="Nutrition notes.")
    raw_text: str | None = Field(
        default=None,
        description="Required for action=sync_text; pasted tracker/export text.",
    )
    limit: int = Field(default=7, ge=1, le=30, description="Maximum recent days to read.")


class BodyOpsAction(StrEnum):
    """Supported body composition operations."""

    SAVE_COMPOSITION = "save_composition"
    GET_RECENT = "get_recent"


class BodyOpsRequest(BaseModel):
    """Typed request for `body_ops`."""

    action: Literal["save_composition", "get_recent"] = Field(
        description="The exact body-composition operation to execute."
    )
    weight_kg: float | None = Field(
        default=None,
        description="Required for action=save_composition; body weight in kilograms.",
    )
    date: str | None = Field(default=None, description="Measurement date in YYYY-MM-DD.")
    body_fat_pct: float | None = Field(default=None, description="Body fat percentage.")
    muscle_mass_pct: float | None = Field(default=None, description="Muscle mass percentage.")
    muscle_mass_kg: float | None = Field(default=None, description="Muscle mass in kilograms.")
    bone_mass_kg: float | None = Field(default=None, description="Bone mass in kilograms.")
    body_water_pct: float | None = Field(default=None, description="Body water percentage.")
    visceral_fat: float | None = Field(default=None, description="Visceral fat reading.")
    bmr: int | None = Field(default=None, description="Basal metabolic rate.")
    bmi: float | None = Field(default=None, description="Body mass index.")
    notes: str | None = Field(default=None, description="Measurement notes.")
    neck_cm: float | None = Field(default=None, description="Neck circumference in cm.")
    chest_cm: float | None = Field(default=None, description="Chest circumference in cm.")
    waist_cm: float | None = Field(default=None, description="Waist circumference in cm.")
    hips_cm: float | None = Field(default=None, description="Hips circumference in cm.")
    bicep_r_cm: float | None = Field(default=None, description="Right bicep circumference in cm.")
    bicep_l_cm: float | None = Field(default=None, description="Left bicep circumference in cm.")
    thigh_r_cm: float | None = Field(default=None, description="Right thigh circumference in cm.")
    thigh_l_cm: float | None = Field(default=None, description="Left thigh circumference in cm.")
    calf_r_cm: float | None = Field(default=None, description="Right calf circumference in cm.")
    calf_l_cm: float | None = Field(default=None, description="Left calf circumference in cm.")
    limit: int = Field(default=10, ge=1, le=30, description="Maximum recent records to read.")


class ScheduleOpsAction(StrEnum):
    """Supported reminder/check-in operations."""

    CREATE_EVENT = "create_event"
    LIST_EVENTS = "list_events"
    UPDATE_EVENT = "update_event"
    DELETE_EVENT = "delete_event"


class ScheduleOpsRequest(BaseModel):
    """Typed request for `schedule_ops`."""

    action: Literal["create_event", "list_events", "update_event", "delete_event"] = Field(
        description="The exact schedule operation to execute."
    )
    event_id: str | None = Field(
        default=None,
        description="Required for update_event and delete_event.",
    )
    title: str | None = Field(default=None, description="Event title.")
    description: str | None = Field(default=None, description="Event description.")
    date: str | None = Field(default=None, description="Event date/time accepted by event service.")
    recurrence: str | None = Field(default=None, description="Recurrence rule or none.")


class MemoryOpsAction(StrEnum):
    """Supported durable-memory operations."""

    SAVE = "save"
    SEARCH = "search"
    UPDATE = "update"
    DELETE = "delete"
    DELETE_BATCH = "delete_batch"


class MemoryOpsRequest(BaseModel):
    """Typed request for `memory_ops`."""

    action: Literal["save", "search", "update", "delete", "delete_batch"] = Field(
        description="The exact memory operation to execute."
    )
    content: str | None = Field(default=None, description="Required for action=save.")
    category: str | None = Field(default=None, description="Memory category for save/search.")
    query: str | None = Field(default=None, description="Required for action=search.")
    memory_id: str | None = Field(default=None, description="Required for update/delete.")
    memory_ids: list[str] | None = Field(default=None, description="Required for delete_batch.")
    new_content: str | None = Field(default=None, description="Required for action=update.")
    limit: int = Field(default=5, ge=1, le=20, description="Maximum memories to read.")


class MetabolismOpsAction(StrEnum):
    """Supported metabolism operations."""

    GET_DATA = "get_data"
    UPDATE_TDEE_PARAMS = "update_tdee_params"
    RESET_TDEE_TRACKING = "reset_tdee_tracking"


class MetabolismOpsRequest(BaseModel):
    """Typed request for `metabolism_ops`."""

    action: Literal["get_data", "update_tdee_params", "reset_tdee_tracking"] = Field(
        description="The exact metabolism operation to execute."
    )
    activity_factor: float | None = Field(
        default=None,
        description="Required for update_tdee_params.",
    )
    reset_tracking: bool = Field(
        default=False,
        description="Whether update_tdee_params should reset tracking.",
    )
    start_date_iso: str | None = Field(
        default=None,
        description="Required for reset_tdee_tracking; ISO date YYYY-MM-DD.",
    )


class ProfileOpsAction(StrEnum):
    """Supported user goal/profile operations."""

    GET_GOAL = "get_goal"
    UPDATE_GOAL = "update_goal"


class ProfileOpsRequest(BaseModel):
    """Typed request for `profile_ops`."""

    action: Literal["get_goal", "update_goal"] = Field(
        description="The exact profile operation to execute."
    )
    goal_type: str | None = Field(default=None, description="Required for update_goal.")
    weekly_rate: float | None = Field(default=None, description="Optional weekly goal rate.")


class RawDataDomain(StrEnum):
    """Raw-data domains available for technical audit."""

    WORKOUTS = "workouts"
    NUTRITION = "nutrition"
    BODY_COMPOSITION = "body_composition"
    GOAL_HISTORY = "goal_history"
    EVENTS = "events"
    MEMORIES = "memories"
    MEMORY_LIST = "memory_list"


class RawDataOpsRequest(BaseModel):
    """Typed request for `raw_data_ops`."""

    domain: Literal[
        "workouts",
        "nutrition",
        "body_composition",
        "goal_history",
        "events",
        "memories",
        "memory_list",
    ] = Field(description="Raw data domain to inspect.")
    start_date: str | None = Field(default=None, description="Optional start date filter.")
    end_date: str | None = Field(default=None, description="Optional end date filter.")
    exercise_name: str | None = Field(default=None, description="Workout exercise name filter.")
    category: str | None = Field(default=None, description="Memory category filter.")
    active_only: bool = Field(default=True, description="Event active-only filter.")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum raw records to return.")
    offset: int = Field(default=0, ge=0, description="Pagination offset.")


class HevyOpsAction(StrEnum):
    """Supported Hevy integration operations."""

    LIST_ROUTINES = "list_routines"
    SEARCH_EXERCISES = "search_exercises"
    GET_ROUTINE_DETAIL = "get_routine_detail"
    CREATE_ROUTINE = "create_routine"
    UPDATE_ROUTINE = "update_routine"
    REPLACE_EXERCISE = "replace_exercise"
    SET_REST_AND_RANGES = "set_rest_and_ranges"
    TRIGGER_IMPORT = "trigger_import"


class HevyOpsRequest(BaseModel):
    """Typed request for `hevy_ops`."""

    action: Literal[
        "list_routines",
        "search_exercises",
        "get_routine_detail",
        "create_routine",
        "update_routine",
        "replace_exercise",
        "set_rest_and_ranges",
        "trigger_import",
    ] = Field(description="The exact Hevy operation to execute.")
    page: int = Field(default=1, ge=1, description="Routine list page.")
    page_size: int = Field(default=10, ge=1, le=50, description="Routine list page size.")
    query: str | None = Field(default=None, description="Required for search_exercises.")
    routine_title_or_id: str | None = Field(
        default=None,
        description="Routine title or ID for read/bulk update operations.",
    )
    routine_title: str | None = Field(
        default=None,
        description="Routine title for update/replace operations.",
    )
    title: str | None = Field(default=None, description="Routine title for create.")
    new_title: str | None = Field(default=None, description="New routine title for update.")
    exercises: list[dict] | None = Field(
        default=None,
        description="Hevy exercise payloads with known template IDs.",
    )
    notes: str | None = Field(default=None, description="Routine notes.")
    allow_structure_rebuild: bool = Field(
        default=False,
        description="Allow rebuilding the routine structure during update.",
    )
    old_exercise_name_or_id: str | None = Field(
        default=None,
        description="Exercise to replace in replace_exercise.",
    )
    new_exercise_id: str | None = Field(
        default=None,
        description="Replacement Hevy exercise template ID.",
    )
    rest_seconds: int = Field(default=90, ge=0, description="Rest time for bulk update.")
    rep_range_start: int = Field(default=8, ge=1, description="Start of rep range.")
    rep_range_end: int = Field(default=12, ge=1, description="End of rep range.")
    days_back: int = Field(default=7, ge=1, le=90, description="Import lookback window.")


def build_chat_tools():
    """Return the small, domain-oriented tools exposed to the chat model."""
    return [
        plan_ops,
        training_ops,
        nutrition_ops,
        body_ops,
        schedule_ops,
        memory_ops,
        metabolism_ops,
        profile_ops,
    ]


def build_hevy_tools():
    """Return Hevy-specific domain tools for turns that need the integration."""
    return [hevy_ops]


def build_raw_data_tools():
    """Return raw/audit domain tools for explicit technical inspection turns."""
    return [raw_data_ops]


def build_legacy_chat_tools():
    """Return legacy fine-grained tools used internally by domain dispatchers."""
    return [
        get_plan_status,
        get_plan,
        plan_help,
        get_plan_training_program,
        update_plan_discovery,
        create_plan_from_discovery,
        update_plan_section,
        record_plan_review,
        get_metabolism_data,
        update_tdee_params,
        reset_tdee_tracking,
        get_user_goal,
        update_user_goal,
        save_workout,
        get_workouts,
        save_daily_nutrition,
        get_nutrition,
        sync_nutrition_text,
        save_body_composition,
        get_body_composition,
        create_event,
        list_events,
        update_event,
        delete_event,
        save_memory,
        search_memory,
        update_memory,
        delete_memory,
        list_raw_memories,
        delete_memories_batch,
        get_workouts_raw,
        get_nutrition_raw,
        get_body_composition_raw,
        get_goal_history_raw,
        get_events_raw,
        get_memories_raw,
        list_hevy_routines,
        search_hevy_exercises,
        get_hevy_routine_detail,
        create_hevy_routine,
        update_hevy_routine,
        replace_hevy_exercise,
        set_routine_rest_and_ranges,
        trigger_hevy_import,
    ]


def build_core_toolset() -> FunctionToolset[ChatAgentDeps]:
    """Build the default toolset sent on ordinary chat turns."""
    return FunctionToolset(
        build_chat_tools(),
        id="core",
        docstring_format="google",
        require_parameter_descriptions=True,
        max_retries=2,
    )


def build_hevy_toolset() -> FunctionToolset[ChatAgentDeps]:
    """Build the optional Hevy toolset for Hevy-specific requests."""
    return FunctionToolset(
        build_hevy_tools(),
        id="hevy",
        docstring_format="google",
        require_parameter_descriptions=True,
        max_retries=2,
    )


def build_raw_data_toolset() -> FunctionToolset[ChatAgentDeps]:
    """Build the optional raw-data toolset for audit/debug requests."""
    return FunctionToolset(
        build_raw_data_tools(),
        id="raw_data",
        docstring_format="google",
        require_parameter_descriptions=True,
        max_retries=2,
    )


def select_chat_toolsets(
    user_input: str,
    runtime_context: dict,
) -> list[FunctionToolset[ChatAgentDeps]]:
    """Select the smallest safe toolset list for the current user turn."""
    selected = [build_core_toolset()]
    lowered = _normalize_intent_text(user_input)
    if _has_hevy_intent(lowered, runtime_context):
        selected.append(build_hevy_toolset())
    if _has_raw_data_intent(lowered):
        selected.append(build_raw_data_toolset())
    _assert_tool_budget(selected)
    return selected


def selected_toolset_summary(
    toolsets: list[FunctionToolset[ChatAgentDeps]],
) -> tuple[list[str], list[str]]:
    """Return selected toolset IDs and model-visible tool names for logging."""
    toolset_ids = [toolset.id or toolset.label for toolset in toolsets]
    tool_names = [
        tool_name
        for toolset in toolsets
        for tool_name in toolset.tools
    ]
    return toolset_ids, tool_names


def _normalize_intent_text(user_input: str) -> str:
    return user_input.strip().lower()


def _has_hevy_intent(lowered_input: str, runtime_context: dict) -> bool:
    hevy_terms = (
        "hevy",
        "rotina externa",
        "routine",
        "template id",
        "template_ids",
        "importar treino",
        "sincronizar treino",
        "sync hevy",
    )
    if any(term in lowered_input for term in hevy_terms):
        return True
    plan_execution = runtime_context.get("plan_execution") or {}
    required_tool = str(plan_execution.get("required_tool") or "")
    return "hevy" in required_tool


def _has_raw_data_intent(lowered_input: str) -> bool:
    raw_terms = (
        "dados brutos",
        "raw",
        "auditoria",
        "auditar",
        "debug",
        "depurar",
        "inspecionar",
        "inspeção",
        "inspecao",
        "exportar",
        "limpeza tecnica",
        "limpeza técnica",
    )
    return any(term in lowered_input for term in raw_terms)


def _assert_tool_budget(toolsets: list[FunctionToolset[ChatAgentDeps]]) -> None:
    tool_count = sum(len(toolset.tools) for toolset in toolsets)
    if tool_count > MAX_AI_TOOLS_PER_TURN:
        raise RuntimeError(
            f"Selected {tool_count} AI tools, above budget {MAX_AI_TOOLS_PER_TURN}."
        )


def _legacy_result(
    *,
    ctx: RunContext[ChatAgentDeps],
    tool_name: str,
    args: dict,
    factory,
    saved: bool = False,
    material_change: bool = False,
    needs_qdrant: bool = False,
    needs_hevy: bool = False,
):
    """Run a legacy operational factory and wrap its result for the agent."""

    def op() -> ToolResult:
        if needs_qdrant and ctx.deps.qdrant_client is None:
            return ToolResult(
                tool_name=tool_name,
                status="blocked",
                saved=False,
                material_change=False,
                message_for_ai="Qdrant indisponivel; nenhuma mudanca foi salva.",
            )
        if needs_hevy and ctx.deps.hevy_service is None:
            return ToolResult(
                tool_name=tool_name,
                status="blocked",
                saved=False,
                material_change=False,
                message_for_ai="Servico Hevy indisponivel; nenhuma mudanca foi salva.",
            )
        tool_obj = factory()
        try:
            output = tool_obj.invoke(args)
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        final_saved, final_material_change, status = _classify_legacy_output(
            output, saved, material_change
        )
        payload = _compact_payload_for_ai(output)
        return ToolResult(
            tool_name=tool_name,
            status=status,
            saved=final_saved,
            material_change=final_material_change,
            message_for_ai=_message_for_ai(output, payload),
            changed_resources=[tool_name] if final_saved else [],
            payload={"result": payload},
        )

    return run_tool(ctx, tool_name, args, op)


async def _legacy_async_result(
    *,
    ctx: RunContext[ChatAgentDeps],
    tool_name: str,
    args: dict,
    factory,
    saved: bool = False,
    material_change: bool = False,
):
    """Run an async legacy operational factory and wrap its result."""

    async def op() -> ToolResult:
        if ctx.deps.hevy_service is None:
            return ToolResult(
                tool_name=tool_name,
                status="blocked",
                saved=False,
                material_change=False,
                message_for_ai="Servico Hevy indisponivel; nenhuma mudanca foi salva.",
            )
        tool_obj = factory()
        try:
            output = await tool_obj.ainvoke(args)
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        final_saved, final_material_change, status = _classify_legacy_output(
            output, saved, material_change
        )
        payload = _compact_payload_for_ai(output)
        return ToolResult(
            tool_name=tool_name,
            status=status,
            saved=final_saved,
            material_change=final_material_change,
            message_for_ai=_message_for_ai(output, payload),
            changed_resources=[tool_name] if final_saved else [],
            payload={"result": payload},
        )

    return await run_async_tool(ctx, tool_name, args, op)


def _classify_legacy_output(
    output,
    requested_saved: bool,
    requested_material_change: bool,
) -> tuple[bool, bool, str]:
    """Classify textual legacy outputs into reliable persistence flags."""
    text = str(output).strip().lower()
    blocker_prefixes = (
        "erro",
        "❌",
        "falha",
        "integração desativada",
        "a integração",
        "perfil do aluno não encontrado",
        "nenhum programa",
        "rotina ",
        "exercício ",
        "o título",
        "a rotina deve",
    )
    if any(text.startswith(prefix) for prefix in blocker_prefixes):
        return False, False, "blocked"
    blocked_terms = (
        " é obrigatório",
        " invalido",
        " inválido",
        "bloqueada",
        "bloqueado",
        "sem permissao",
        "sem permissão",
        "limite atingido",
        "nao puderam ser recuperados",
        "não puderam ser recuperados",
        "verifique os dados",
    )
    if any(term in text for term in blocked_terms):
        return False, False, "blocked"
    if (
        "não encontrada" in text
        or "não encontrado" in text
        or "nao encontrada" in text
        or "nao encontrado" in text
    ):
        return False, False, "not_found"
    return requested_saved, requested_material_change, "success"


def _compact_payload_for_ai(output):
    if isinstance(output, dict):
        compact = dict(output)
        items = compact.get("items")
        if isinstance(items, list) and len(items) > 10:
            compact["items"] = items[:10]
            compact["truncated_items"] = len(items) - 10
        return compact
    if isinstance(output, list):
        if len(output) > 10:
            return {"items": output[:10], "total": len(output), "truncated_items": len(output) - 10}
        return output
    return output


def _message_for_ai(output, compact_payload) -> str:
    if isinstance(output, (dict, list)):
        return json.dumps(compact_payload, ensure_ascii=False, default=str)
    return str(output)


def _action_label(action: str | StrEnum) -> str:
    return action.value if isinstance(action, StrEnum) else action


def _require(value, field_name: str, action: str | StrEnum):
    if value is None or value == "":
        raise ModelRetry(f"{field_name} e obrigatorio para action={_action_label(action)}.")
    return value


def _validate_action_payload(
    model_type,
    payload: dict[str, Any] | None,
    action: str | StrEnum,
):
    raw_payload = _require(payload, "payload", action)
    try:
        return model_type.model_validate(raw_payload)
    except ValueError as exc:
        raise ModelRetry(f"payload invalido para action={_action_label(action)}: {exc}") from exc


def _validation_error_result(tool_name: str, action: str | StrEnum, message: str) -> ToolResult:
    return ToolResult(
        tool_name=tool_name,
        status="validation_error",
        saved=False,
        material_change=False,
        message_for_ai=message,
        retryable=True,
        validation_errors=[
            {"msg": message, "type": "validation_error", "action": _action_label(action)}
        ],
    )


def plan_ops(ctx: RunContext[ChatAgentDeps], request: PlanOpsRequest) -> ToolResult:
    """Execute plan lifecycle operations through one clear domain tool.

    Use when the user asks about plan status, wants to create a first plan,
    approves a pending plan change, requests an active-plan edit, or needs the
    training program stored in the active plan. Do not use for ordinary workout
    logs, Hevy routine edits, reminders, memories, or body measurements.

    Args:
        request: Plan action plus the typed payload required by that action.
    """
    if request.action == PlanOpsAction.GET_STATUS:
        return get_plan_status(ctx)
    if request.action == PlanOpsAction.GET_PLAN:
        return get_plan(ctx)
    if request.action == PlanOpsAction.HELP:
        return plan_help(ctx)
    if request.action == PlanOpsAction.GET_TRAINING_PROGRAM:
        return get_plan_training_program(ctx, output_format=request.output_format)
    if request.action == PlanOpsAction.UPDATE_DISCOVERY:
        try:
            payload = _validate_action_payload(
                PlanDiscoveryUpdateInput,
                request.payload,
                request.action,
            )
        except ModelRetry as exc:
            return _validation_error_result("plan_ops", request.action, str(exc))
        return update_plan_discovery(ctx, payload)
    if request.action == PlanOpsAction.CREATE_FROM_DISCOVERY:
        try:
            payload = _validate_action_payload(PlanCreateInput, request.payload, request.action)
        except ModelRetry as exc:
            return _validation_error_result("plan_ops", request.action, str(exc))
        return create_plan_from_discovery(ctx, payload)
    if request.action == PlanOpsAction.UPDATE_SECTION:
        try:
            payload = _validate_action_payload(
                PlanSectionUpdateInput,
                request.payload,
                request.action,
            )
        except ModelRetry as exc:
            return _validation_error_result("plan_ops", request.action, str(exc))
        return update_plan_section(ctx, payload)
    if request.action == PlanOpsAction.RECORD_REVIEW:
        try:
            payload = _validate_action_payload(PlanReviewInput, request.payload, request.action)
        except ModelRetry as exc:
            return _validation_error_result("plan_ops", request.action, str(exc))
        return record_plan_review(ctx, payload)
    raise ModelRetry(f"action desconhecida para plan_ops: {request.action}.")


def training_ops(ctx: RunContext[ChatAgentDeps], request: TrainingOpsRequest) -> ToolResult:
    """Read or persist workout logs through one training-domain tool.

    Use for completed workout history: saving a workout the user performed or
    reading recent workout logs. Do not use for active plan edits, Hevy routine
    templates, nutrition totals, or body measurements.

    Args:
        request: Training action plus workout details or read limit.
    """
    if request.action == TrainingOpsAction.GET_WORKOUTS:
        return get_workouts(ctx, limit=request.limit)
    if request.action == TrainingOpsAction.SAVE_WORKOUT:
        workout_type = _require(request.workout_type, "workout_type", request.action)
        exercises = _require(request.exercises, "exercises", request.action)
        return save_workout(
            ctx,
            workout_type=workout_type,
            exercises=exercises,
            date=request.date,
            duration_minutes=request.duration_minutes,
            notes=request.notes,
        )
    raise ModelRetry(f"action desconhecida para training_ops: {request.action}.")


def nutrition_ops(ctx: RunContext[ChatAgentDeps], request: NutritionOpsRequest) -> ToolResult:
    """Read, save, or import nutrition data through one nutrition-domain tool.

    Use for consumed food totals, recent nutrition history, or pasted tracker
    text. Do not use this for calorie targets in a plan unless paired with
    plan/metabolism tools as needed.

    Args:
        request: Nutrition action plus totals, import text, or read limit.
    """
    if request.action == NutritionOpsAction.GET_RECENT:
        return get_nutrition(ctx, limit=request.limit)
    if request.action == NutritionOpsAction.SYNC_TEXT:
        raw_text = _require(request.raw_text, "raw_text", request.action)
        return sync_nutrition_text(ctx, raw_text=raw_text)
    if request.action == NutritionOpsAction.SAVE_DAILY_TOTALS:
        calories = _require(request.calories, "calories", request.action)
        return save_daily_nutrition(
            ctx,
            calories=calories,
            protein_grams=request.protein_grams,
            carbs_grams=request.carbs_grams,
            fat_grams=request.fat_grams,
            fiber_grams=request.fiber_grams,
            date=request.date,
            notes=request.notes,
        )
    raise ModelRetry(f"action desconhecida para nutrition_ops: {request.action}.")


def body_ops(ctx: RunContext[ChatAgentDeps], request: BodyOpsRequest) -> ToolResult:
    """Read or persist body-composition measurements through one domain tool.

    Use for weight, scale readings, body-fat estimates, circumferences, and
    recent body-composition history. Do not use for workout logs or plan edits.

    Args:
        request: Body-composition action plus measurements or read limit.
    """
    if request.action == BodyOpsAction.GET_RECENT:
        return get_body_composition(ctx, limit=request.limit)
    if request.action == BodyOpsAction.SAVE_COMPOSITION:
        weight_kg = _require(request.weight_kg, "weight_kg", request.action)
        return save_body_composition(
            ctx,
            weight_kg=weight_kg,
            date=request.date,
            body_fat_pct=request.body_fat_pct,
            muscle_mass_pct=request.muscle_mass_pct,
            muscle_mass_kg=request.muscle_mass_kg,
            bone_mass_kg=request.bone_mass_kg,
            body_water_pct=request.body_water_pct,
            visceral_fat=request.visceral_fat,
            bmr=request.bmr,
            bmi=request.bmi,
            notes=request.notes,
            neck_cm=request.neck_cm,
            chest_cm=request.chest_cm,
            waist_cm=request.waist_cm,
            hips_cm=request.hips_cm,
            bicep_r_cm=request.bicep_r_cm,
            bicep_l_cm=request.bicep_l_cm,
            thigh_r_cm=request.thigh_r_cm,
            thigh_l_cm=request.thigh_l_cm,
            calf_r_cm=request.calf_r_cm,
            calf_l_cm=request.calf_l_cm,
        )
    raise ModelRetry(f"action desconhecida para body_ops: {request.action}.")


def schedule_ops(ctx: RunContext[ChatAgentDeps], request: ScheduleOpsRequest) -> ToolResult:
    """Manage reminders and check-in events through one schedule-domain tool.

    Use for agenda reminders, check-ins, recurring events, and deleting/updating
    those events by ID. Do not use for creating training plans.

    Args:
        request: Schedule action plus event fields or event ID.
    """
    if request.action == ScheduleOpsAction.LIST_EVENTS:
        return list_events(ctx)
    if request.action == ScheduleOpsAction.CREATE_EVENT:
        title = _require(request.title, "title", request.action)
        return create_event(
            ctx,
            title=title,
            description=request.description,
            date=request.date,
            recurrence=request.recurrence or "none",
        )
    if request.action == ScheduleOpsAction.UPDATE_EVENT:
        event_id = _require(request.event_id, "event_id", request.action)
        return update_event(
            ctx,
            event_id=event_id,
            title=request.title,
            description=request.description,
            date=request.date,
            recurrence=request.recurrence,
        )
    if request.action == ScheduleOpsAction.DELETE_EVENT:
        event_id = _require(request.event_id, "event_id", request.action)
        return delete_event(ctx, event_id=event_id)
    raise ModelRetry(f"action desconhecida para schedule_ops: {request.action}.")


def memory_ops(ctx: RunContext[ChatAgentDeps], request: MemoryOpsRequest) -> ToolResult:
    """Search or mutate durable user memories through one memory-domain tool.

    Use for long-term preferences, constraints, duplicate checks, and explicit
    memory cleanup. Search before saving when duplicate memories are possible.

    Args:
        request: Memory action plus content, query, IDs, or limit.
    """
    if request.action == MemoryOpsAction.SEARCH:
        query = _require(request.query, "query", request.action)
        return search_memory(ctx, query=query, limit=request.limit)
    if request.action == MemoryOpsAction.SAVE:
        content = _require(request.content, "content", request.action)
        category = _require(request.category, "category", request.action)
        return save_memory(ctx, content=content, category=category)
    if request.action == MemoryOpsAction.UPDATE:
        memory_id = _require(request.memory_id, "memory_id", request.action)
        new_content = _require(request.new_content, "new_content", request.action)
        return update_memory(ctx, memory_id=memory_id, new_content=new_content)
    if request.action == MemoryOpsAction.DELETE:
        memory_id = _require(request.memory_id, "memory_id", request.action)
        return delete_memory(ctx, memory_id=memory_id)
    if request.action == MemoryOpsAction.DELETE_BATCH:
        memory_ids = _require(request.memory_ids, "memory_ids", request.action)
        return delete_memories_batch(ctx, memory_ids=memory_ids)
    raise ModelRetry(f"action desconhecida para memory_ops: {request.action}.")


def metabolism_ops(ctx: RunContext[ChatAgentDeps], request: MetabolismOpsRequest) -> ToolResult:
    """Read or mutate adaptive metabolism settings through one domain tool.

    Use before calorie/macros recommendations, plan nutrition creation, TDEE
    parameter changes, or explicit TDEE tracking resets.

    Args:
        request: Metabolism action plus activity factor or reset date when needed.
    """
    if request.action == MetabolismOpsAction.GET_DATA:
        return get_metabolism_data(ctx)
    if request.action == MetabolismOpsAction.UPDATE_TDEE_PARAMS:
        activity_factor = _require(request.activity_factor, "activity_factor", request.action)
        return update_tdee_params(
            ctx,
            activity_factor=activity_factor,
            reset_tracking=request.reset_tracking,
        )
    if request.action == MetabolismOpsAction.RESET_TDEE_TRACKING:
        start_date_iso = _require(request.start_date_iso, "start_date_iso", request.action)
        return reset_tdee_tracking(ctx, start_date_iso=start_date_iso)
    raise ModelRetry(f"action desconhecida para metabolism_ops: {request.action}.")


def profile_ops(ctx: RunContext[ChatAgentDeps], request: ProfileOpsRequest) -> ToolResult:
    """Read or update the user's explicit goal profile.

    Use for goal profile reads and explicit goal changes. Do not use this as a
    substitute for active-plan edits; use `plan_ops` for plan strategy changes.

    Args:
        request: Profile action plus goal fields when updating.
    """
    if request.action == ProfileOpsAction.GET_GOAL:
        return get_user_goal(ctx)
    if request.action == ProfileOpsAction.UPDATE_GOAL:
        goal_type = _require(request.goal_type, "goal_type", request.action)
        return update_user_goal(ctx, goal_type=goal_type, weekly_rate=request.weekly_rate)
    raise ModelRetry(f"action desconhecida para profile_ops: {request.action}.")


def raw_data_ops(ctx: RunContext[ChatAgentDeps], request: RawDataOpsRequest) -> ToolResult:
    """Read raw records only for explicit audit, debug, export, or cleanup.

    Use only when the user explicitly asks for raw data, technical inspection,
    audit, export, or cleanup. Prefer summary/domain tools for normal coaching.

    Args:
        request: Raw-data domain plus optional filters and pagination.
    """
    if request.domain == RawDataDomain.WORKOUTS:
        return get_workouts_raw(
            ctx,
            start_date=request.start_date,
            end_date=request.end_date,
            exercise_name=request.exercise_name,
            limit=request.limit,
            offset=request.offset,
        )
    if request.domain == RawDataDomain.NUTRITION:
        return get_nutrition_raw(
            ctx,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset,
        )
    if request.domain == RawDataDomain.BODY_COMPOSITION:
        return get_body_composition_raw(
            ctx,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset,
        )
    if request.domain == RawDataDomain.GOAL_HISTORY:
        return get_goal_history_raw(ctx)
    if request.domain == RawDataDomain.EVENTS:
        return get_events_raw(
            ctx,
            start_date=request.start_date,
            end_date=request.end_date,
            active_only=request.active_only,
            limit=request.limit,
            offset=request.offset,
        )
    if request.domain == RawDataDomain.MEMORIES:
        return get_memories_raw(
            ctx,
            category=request.category,
            limit=request.limit,
            offset=request.offset,
        )
    if request.domain == RawDataDomain.MEMORY_LIST:
        return list_raw_memories(ctx, limit=request.limit)
    raise ModelRetry(f"domain desconhecido para raw_data_ops: {request.domain}.")


async def hevy_ops(ctx: RunContext[ChatAgentDeps], request: HevyOpsRequest) -> ToolResult:
    """Operate the Hevy integration when the user explicitly asks for Hevy work.

    Use for Hevy routines, Hevy exercise template search, routine structure
    changes, and importing recent Hevy workouts. Do not use for ordinary local
    workout logs or active-plan text unless Hevy sync is explicitly involved.

    Args:
        request: Hevy action plus routine, exercise, or import parameters.
    """
    if request.action == HevyOpsAction.LIST_ROUTINES:
        return await list_hevy_routines(ctx, page=request.page, page_size=request.page_size)
    if request.action == HevyOpsAction.SEARCH_EXERCISES:
        query = _require(request.query, "query", request.action)
        return await search_hevy_exercises(ctx, query=query)
    if request.action == HevyOpsAction.GET_ROUTINE_DETAIL:
        routine_title_or_id = _require(
            request.routine_title_or_id,
            "routine_title_or_id",
            request.action,
        )
        return await get_hevy_routine_detail(ctx, routine_title_or_id=routine_title_or_id)
    if request.action == HevyOpsAction.CREATE_ROUTINE:
        title = _require(request.title, "title", request.action)
        exercises = _require(request.exercises, "exercises", request.action)
        return await create_hevy_routine(
            ctx,
            title=title,
            exercises=exercises,
            notes=request.notes,
        )
    if request.action == HevyOpsAction.UPDATE_ROUTINE:
        routine_title = _require(request.routine_title, "routine_title", request.action)
        return await update_hevy_routine(
            ctx,
            routine_title=routine_title,
            new_title=request.new_title,
            exercises=request.exercises,
            notes=request.notes,
            allow_structure_rebuild=request.allow_structure_rebuild,
        )
    if request.action == HevyOpsAction.REPLACE_EXERCISE:
        routine_title = _require(request.routine_title, "routine_title", request.action)
        old_exercise = _require(
            request.old_exercise_name_or_id,
            "old_exercise_name_or_id",
            request.action,
        )
        new_exercise_id = _require(request.new_exercise_id, "new_exercise_id", request.action)
        return await replace_hevy_exercise(
            ctx,
            routine_title=routine_title,
            old_exercise_name_or_id=old_exercise,
            new_exercise_id=new_exercise_id,
        )
    if request.action == HevyOpsAction.SET_REST_AND_RANGES:
        routine_title_or_id = _require(
            request.routine_title_or_id,
            "routine_title_or_id",
            request.action,
        )
        return await set_routine_rest_and_ranges(
            ctx,
            routine_title_or_id=routine_title_or_id,
            rest_seconds=request.rest_seconds,
            rep_range_start=request.rep_range_start,
            rep_range_end=request.rep_range_end,
        )
    if request.action == HevyOpsAction.TRIGGER_IMPORT:
        return await trigger_hevy_import(ctx, days_back=request.days_back)
    raise ModelRetry(f"action desconhecida para hevy_ops: {request.action}.")


def plan_help(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """
    Explain the operational contract for plan tools.

    Use when the model needs the exact plan lifecycle before creating or
    updating a plan. This is read-only and never changes user data.
    """

    def op() -> ToolResult:
        return ToolResult(
            tool_name="plan_help",
            status="success",
            message_for_ai=(
                "Fluxo: use plan_ops(action=get_status). Sem plano ativo, colete "
                "discovery com plan_ops(action=update_discovery) ate nao haver "
                "missing_fields; chame metabolism_ops(action=get_data); crie com "
                "plan_ops(action=create_from_discovery). Com plano ativo, altere "
                "secoes tipadas com plan_ops(action=update_section) e registre "
                "revisoes com plan_ops(action=record_review). saved=false nunca "
                "permite afirmar sucesso."
            ),
        )

    return run_tool(ctx, "plan_help", {}, op)


def get_plan_status(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """
    Return the user's current plan lifecycle status.

    Use before any plan creation/update decision. Read-only.
    """

    def op() -> ToolResult:
        db = ctx.deps.database
        plan = db.get_plan(ctx.deps.user_email)
        if plan is not None:
            progress = build_progress_snapshot(plan, db)
            view = build_plan_view_model(plan, None, progress)
            return ToolResult(
                tool_name="get_plan_status",
                status="ACTIVE_PLAN",
                message_for_ai="Existe plano ativo.",
                payload={"plan_id": plan.id, "view": view.model_dump()},
            )
        discovery = db.get_plan_discovery(ctx.deps.user_email)
        missing = missing_discovery_fields(discovery)
        return ToolResult(
            tool_name="get_plan_status",
            status="DISCOVERY_IN_PROGRESS" if discovery else "NO_PLAN",
            message_for_ai=(
                "Discovery em andamento."
                if discovery
                else "Nao existe plano ativo nem discovery iniciado."
            ),
            payload={
                "missing_fields": missing,
                "discovery": discovery.model_dump() if discovery else None,
            },
        )

    return run_tool(ctx, "get_plan_status", {}, op)


def get_plan(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """
    Return the full active plan JSON.

    Use only when the answer needs actual plan details. Read-only.
    """

    def op() -> ToolResult:
        plan = ctx.deps.database.get_plan(ctx.deps.user_email)
        if plan is None:
            return ToolResult(
                tool_name="get_plan",
                status="NO_PLAN",
                message_for_ai="Nao existe plano ativo.",
                payload=None,
            )
        return ToolResult(
            tool_name="get_plan",
            status="ACTIVE_PLAN",
            message_for_ai="Plano ativo carregado.",
            payload=plan.model_dump(),
        )

    return run_tool(ctx, "get_plan", {}, op)


def update_plan_discovery(
    ctx: RunContext[ChatAgentDeps], payload: PlanDiscoveryUpdateInput
) -> ToolResult:
    """
    Persist incremental discovery answers for first plan creation.

    Use when the user provides goal, deadline, weekly availability,
    restrictions, preferences, equipment, or similar discovery data. Do not use
    to change an already active plan.
    """

    def op() -> ToolResult:
        db = ctx.deps.database
        current = db.get_plan_discovery(ctx.deps.user_email)
        discovery = apply_discovery_update(ctx.deps.user_email, current, payload)
        discovery_id = db.save_plan_discovery(discovery)
        return ToolResult(
            tool_name="update_plan_discovery",
            status="discovery_updated",
            saved=True,
            material_change=False,
            message_for_ai="Discovery atualizado. Continue com o proximo bloqueio.",
            changed_resources=["plan_discovery"],
            payload={
                "discovery_id": discovery_id,
                "missing_fields": discovery.missing_fields,
            },
        )

    return run_tool(ctx, "update_plan_discovery", {"payload": payload.model_dump()}, op)


def create_plan_from_discovery(
    ctx: RunContext[ChatAgentDeps], payload: PlanCreateInput
) -> ToolResult:
    """
    Create the first active plan from complete discovery.

    Use only when discovery has no missing fields and metabolism data was read
    in this turn. This mutates the active plan and clears discovery.
    """

    def op() -> ToolResult:
        db = ctx.deps.database
        discovery = db.get_plan_discovery(ctx.deps.user_email)
        missing = missing_discovery_fields(discovery)
        if missing:
            return ToolResult(
                tool_name="create_plan_from_discovery",
                status="blocked",
                saved=False,
                material_change=False,
                message_for_ai=f"Discovery incompleto: {', '.join(missing)}.",
                payload={"missing_fields": missing},
            )
        try:
            plan = build_plan_from_create_input(ctx.deps.user_email, payload)
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        plan_id = db.save_plan(plan)
        db.clear_plan_discovery(ctx.deps.user_email)
        return ToolResult(
            tool_name="create_plan_from_discovery",
            status="success",
            saved=True,
            material_change=True,
            message_for_ai="Plano criado com sucesso.",
            changed_resources=["plan"],
            payload={"plan_id": plan_id},
        )

    return run_tool(ctx, "create_plan_from_discovery", {"payload": payload.model_dump()}, op)


def update_plan_section(
    ctx: RunContext[ChatAgentDeps], payload: PlanSectionUpdateInput
) -> ToolResult:
    """
    Update typed sections of the active plan.

    Use for changing goal, timeline, user_context, training, nutrition,
    alignment, or tracking. Never claim the plan changed unless this returns
    saved=true and material_change=true.
    """

    def op() -> ToolResult:
        db = ctx.deps.database
        current = db.get_plan(ctx.deps.user_email)
        if current is None:
            return ToolResult(
                tool_name="update_plan_section",
                status="not_found",
                saved=False,
                message_for_ai="Nao existe plano ativo para atualizar.",
                payload={"missing_fields": ["active_plan"]},
            )
        try:
            updated = merge_plan_section(current, payload)
            if payload.section == "training":
                updated = sync_training_with_hevy_if_needed(
                    database=db,
                    user_email=ctx.deps.user_email,
                    current_plan=current,
                    updated_plan=updated,
                )
            plan_id = db.save_plan(updated)
        except HevySyncError as exc:
            return ToolResult(
                tool_name="update_plan_section",
                status="external_error",
                saved=False,
                external_sync_failed=True,
                message_for_ai=str(exc),
            )
        except ValueError as exc:
            raise ModelRetry(str(exc)) from exc
        return ToolResult(
            tool_name="update_plan_section",
            status="success",
            saved=True,
            material_change=True,
            message_for_ai="Plano atualizado com sucesso.",
            changed_resources=["plan"],
            payload={"plan_id": plan_id},
        )

    return run_tool(ctx, "update_plan_section", {"payload": payload.model_dump()}, op)


def record_plan_review(
    ctx: RunContext[ChatAgentDeps], payload: PlanReviewInput
) -> ToolResult:
    """
    Record evidence and decision for a plan review.

    Use after evaluating progress. This saves review history but does not
    necessarily change the active plan strategy.
    """

    def op() -> ToolResult:
        db = ctx.deps.database
        current = db.get_plan(ctx.deps.user_email)
        if current is None:
            return ToolResult(
                tool_name="record_plan_review",
                status="not_found",
                saved=False,
                message_for_ai="Nao existe plano ativo para revisar.",
            )
        review = build_review_record(payload)
        updated = attach_review(current, review)
        plan_id = db.save_plan(updated)
        return ToolResult(
            tool_name="record_plan_review",
            status="review_recorded",
            saved=True,
            material_change=False,
            message_for_ai="Revisao registrada sem mudar o plano ativo.",
            changed_resources=["plan_review"],
            payload={"plan_id": plan_id},
        )

    return run_tool(ctx, "record_plan_review", {"payload": payload.model_dump()}, op)


def get_metabolism_data(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """
    Return official adaptive metabolism data and daily targets.

    Use before recommending calories/macros or creating/changing nutrition
    strategy. Read-only.
    """

    def op() -> ToolResult:
        data = AdaptiveTDEEService(ctx.deps.database).calculate_tdee(ctx.deps.user_email)
        return ToolResult(
            tool_name="get_metabolism_data",
            status="success",
            message_for_ai="Dados metabolicos oficiais carregados.",
            payload=data or {},
        )

    return run_tool(ctx, "get_metabolism_data", {}, op)


def get_plan_training_program(
    ctx: RunContext[ChatAgentDeps], output_format: str = "text"
) -> ToolResult:
    """Read the training program stored in the active plan. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_plan_training_program",
        args={"output_format": output_format},
        factory=lambda: create_get_plan_training_program_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def update_tdee_params(
    ctx: RunContext[ChatAgentDeps],
    activity_factor: float,
    reset_tracking: bool = False,
) -> ToolResult:
    """Update adaptive TDEE parameters. Mutates metabolism settings."""
    return _legacy_result(
        ctx=ctx,
        tool_name="update_tdee_params",
        args={"activity_factor": activity_factor, "reset_tracking": reset_tracking},
        factory=lambda: create_update_tdee_params_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def reset_tdee_tracking(ctx: RunContext[ChatAgentDeps], start_date_iso: str) -> ToolResult:
    """Reset adaptive TDEE tracking from a confirmed ISO date. Mutates history."""
    return _legacy_result(
        ctx=ctx,
        tool_name="reset_tdee_tracking",
        args={"start_date_iso": start_date_iso},
        factory=lambda: create_reset_tdee_tracking_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def get_user_goal(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """Read the user's current goal profile before goal-sensitive advice."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_user_goal",
        args={},
        factory=lambda: create_get_user_goal_tool(ctx.deps.database, ctx.deps.user_email),
    )


def update_user_goal(
    ctx: RunContext[ChatAgentDeps], goal_type: str, weekly_rate: float | None = None
) -> ToolResult:
    """Update the user's explicit goal after a clear user instruction."""
    return _legacy_result(
        ctx=ctx,
        tool_name="update_user_goal",
        args={"goal_type": goal_type, "weekly_rate": weekly_rate},
        factory=lambda: create_update_user_goal_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def save_workout(
    ctx: RunContext[ChatAgentDeps],
    workout_type: str,
    exercises: list[dict],
    date: str | None = None,
    duration_minutes: int | None = None,
    notes: str | None = None,
) -> ToolResult:
    """Persist a completed workout log. Use only for actual workout data."""
    return _legacy_result(
        ctx=ctx,
        tool_name="save_workout",
        args={
            "workout_type": workout_type,
            "exercises": exercises,
            "date": date,
            "duration_minutes": duration_minutes,
            "notes": notes,
        },
        factory=lambda: create_save_workout_tool(ctx.deps.database, ctx.deps.user_email),
        saved=True,
        material_change=True,
    )


def get_workouts(ctx: RunContext[ChatAgentDeps], limit: int = 5) -> ToolResult:
    """Read recent workout logs. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_workouts",
        args={"limit": limit},
        factory=lambda: create_get_workouts_tool(ctx.deps.database, ctx.deps.user_email),
    )


def save_daily_nutrition(
    ctx: RunContext[ChatAgentDeps],
    calories: int | float | str,
    protein_grams: float | str | None = None,
    carbs_grams: float | str | None = None,
    fat_grams: float | str | None = None,
    fiber_grams: float | str | None = None,
    date: str | None = None,
    notes: str | None = None,
) -> ToolResult:
    """Persist daily nutrition totals. Use for consumed food totals, not targets."""
    return _legacy_result(
        ctx=ctx,
        tool_name="save_daily_nutrition",
        args={
            "calories": calories,
            "protein_grams": protein_grams,
            "carbs_grams": carbs_grams,
            "fat_grams": fat_grams,
            "fiber_grams": fiber_grams,
            "date": date,
            "notes": notes,
        },
        factory=lambda: create_save_nutrition_tool(ctx.deps.database, ctx.deps.user_email),
        saved=True,
        material_change=True,
    )


def get_nutrition(ctx: RunContext[ChatAgentDeps], limit: int = 7) -> ToolResult:
    """Read recent nutrition logs. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_nutrition",
        args={"limit": limit},
        factory=lambda: create_get_nutrition_tool(ctx.deps.database, ctx.deps.user_email),
    )


def sync_nutrition_text(ctx: RunContext[ChatAgentDeps], raw_text: str) -> ToolResult:
    """Parse and persist nutrition totals from imported tracker text."""
    return _legacy_result(
        ctx=ctx,
        tool_name="sync_nutrition_text",
        args={"raw_text": raw_text},
        factory=lambda: create_sync_nutrition_text_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def save_body_composition(
    ctx: RunContext[ChatAgentDeps],
    weight_kg: float,
    date: str | None = None,
    body_fat_pct: float | None = None,
    muscle_mass_pct: float | None = None,
    muscle_mass_kg: float | None = None,
    bone_mass_kg: float | None = None,
    body_water_pct: float | None = None,
    visceral_fat: float | None = None,
    bmr: int | None = None,
    bmi: float | None = None,
    notes: str | None = None,
    neck_cm: float | None = None,
    chest_cm: float | None = None,
    waist_cm: float | None = None,
    hips_cm: float | None = None,
    bicep_r_cm: float | None = None,
    bicep_l_cm: float | None = None,
    thigh_r_cm: float | None = None,
    thigh_l_cm: float | None = None,
    calf_r_cm: float | None = None,
    calf_l_cm: float | None = None,
) -> ToolResult:
    """Persist body composition data from scale, tape, or wearable readings."""
    args = locals().copy()
    args.pop("ctx")
    return _legacy_result(
        ctx=ctx,
        tool_name="save_body_composition",
        args=args,
        factory=lambda: create_save_composition_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def get_body_composition(ctx: RunContext[ChatAgentDeps], limit: int = 10) -> ToolResult:
    """Read recent body composition and measurements. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_body_composition",
        args={"limit": limit},
        factory=lambda: create_get_composition_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def create_event(
    ctx: RunContext[ChatAgentDeps],
    title: str,
    description: str | None = None,
    date: str | None = None,
    recurrence: str = "none",
) -> ToolResult:
    """Create a reminder/check-in event. Do not use for plan creation."""
    return _legacy_result(
        ctx=ctx,
        tool_name="create_event",
        args={
            "title": title,
            "description": description,
            "date": date,
            "recurrence": recurrence,
        },
        factory=lambda: create_create_event_tool(
            ctx.deps.database.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def list_events(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """List active reminders/check-ins. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="list_events",
        args={},
        factory=lambda: create_list_events_tool(
            ctx.deps.database.database, ctx.deps.user_email
        ),
    )


def update_event(
    ctx: RunContext[ChatAgentDeps],
    event_id: str,
    title: str | None = None,
    description: str | None = None,
    date: str | None = None,
    recurrence: str | None = None,
) -> ToolResult:
    """Update an existing reminder/check-in by ID."""
    return _legacy_result(
        ctx=ctx,
        tool_name="update_event",
        args={
            "event_id": event_id,
            "title": title,
            "description": description,
            "date": date,
            "recurrence": recurrence,
        },
        factory=lambda: create_update_event_tool(
            ctx.deps.database.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def delete_event(ctx: RunContext[ChatAgentDeps], event_id: str) -> ToolResult:
    """Delete an existing reminder/check-in by ID."""
    return _legacy_result(
        ctx=ctx,
        tool_name="delete_event",
        args={"event_id": event_id},
        factory=lambda: create_delete_event_tool(
            ctx.deps.database.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


def save_memory(ctx: RunContext[ChatAgentDeps], content: str, category: str) -> ToolResult:
    """Save a durable user memory after searching for duplicates first."""
    return _legacy_result(
        ctx=ctx,
        tool_name="save_memory",
        args={"content": content, "category": category},
        factory=lambda: create_save_memory_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
        needs_qdrant=True,
    )


def search_memory(ctx: RunContext[ChatAgentDeps], query: str, limit: int = 5) -> ToolResult:
    """Search durable user memories before personalized advice or save/update."""
    return _legacy_result(
        ctx=ctx,
        tool_name="search_memory",
        args={"query": query, "limit": limit},
        factory=lambda: create_search_memory_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        needs_qdrant=True,
    )


def update_memory(
    ctx: RunContext[ChatAgentDeps], memory_id: str, new_content: str
) -> ToolResult:
    """Update one durable memory by ID after confirming it exists."""
    return _legacy_result(
        ctx=ctx,
        tool_name="update_memory",
        args={"memory_id": memory_id, "new_content": new_content},
        factory=lambda: create_update_memory_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
        needs_qdrant=True,
    )


def delete_memory(ctx: RunContext[ChatAgentDeps], memory_id: str) -> ToolResult:
    """Delete one durable memory by ID after explicit user intent."""
    return _legacy_result(
        ctx=ctx,
        tool_name="delete_memory",
        args={"memory_id": memory_id},
        factory=lambda: create_delete_memory_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
        needs_qdrant=True,
    )


def list_raw_memories(ctx: RunContext[ChatAgentDeps], limit: int = 50) -> ToolResult:
    """List raw memories for audit and cleanup. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="list_raw_memories",
        args={"limit": limit},
        factory=lambda: create_list_raw_memories_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        needs_qdrant=True,
    )


def delete_memories_batch(
    ctx: RunContext[ChatAgentDeps], memory_ids: list[str]
) -> ToolResult:
    """Delete multiple memories by explicit IDs after user confirmation."""
    return _legacy_result(
        ctx=ctx,
        tool_name="delete_memories_batch",
        args={"memory_ids": memory_ids},
        factory=lambda: create_delete_memories_batch_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
        needs_qdrant=True,
    )


def get_workouts_raw(
    ctx: RunContext[ChatAgentDeps],
    start_date: str | None = None,
    end_date: str | None = None,
    exercise_name: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ToolResult:
    """Return raw workout documents for analysis/debugging. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_workouts_raw",
        args={
            "start_date": start_date,
            "end_date": end_date,
            "exercise_name": exercise_name,
            "limit": limit,
            "offset": offset,
        },
        factory=lambda: create_get_workouts_raw_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def get_nutrition_raw(
    ctx: RunContext[ChatAgentDeps],
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ToolResult:
    """Return raw nutrition documents for analysis/debugging. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_nutrition_raw",
        args={
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        },
        factory=lambda: create_get_nutrition_raw_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def get_body_composition_raw(
    ctx: RunContext[ChatAgentDeps],
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ToolResult:
    """Return raw body composition documents. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_body_composition_raw",
        args={
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit,
            "offset": offset,
        },
        factory=lambda: create_get_body_composition_raw_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def get_goal_history_raw(ctx: RunContext[ChatAgentDeps]) -> ToolResult:
    """Return raw goal/profile history for audit. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_goal_history_raw",
        args={},
        factory=lambda: create_get_goal_history_raw_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def get_events_raw(
    ctx: RunContext[ChatAgentDeps],
    start_date: str | None = None,
    end_date: str | None = None,
    active_only: bool = True,
    limit: int = 50,
    offset: int = 0,
) -> ToolResult:
    """Return raw scheduled event documents. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_events_raw",
        args={
            "start_date": start_date,
            "end_date": end_date,
            "active_only": active_only,
            "limit": limit,
            "offset": offset,
        },
        factory=lambda: create_get_events_raw_tool(
            ctx.deps.database, ctx.deps.user_email
        ),
    )


def get_memories_raw(
    ctx: RunContext[ChatAgentDeps],
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> ToolResult:
    """Return raw memory vectors/payloads for audit. Read-only."""
    return _legacy_result(
        ctx=ctx,
        tool_name="get_memories_raw",
        args={"category": category, "limit": limit, "offset": offset},
        factory=lambda: create_get_memories_raw_tool(
            ctx.deps.qdrant_client, ctx.deps.user_email
        ),
        needs_qdrant=True,
    )


async def list_hevy_routines(
    ctx: RunContext[ChatAgentDeps], page: int = 1, page_size: int = 10
) -> ToolResult:
    """List the user's Hevy routines. Read-only and Hevy-specific."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="list_hevy_routines",
        args={"page": page, "page_size": page_size},
        factory=lambda: create_list_hevy_routines_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
    )


async def search_hevy_exercises(
    ctx: RunContext[ChatAgentDeps], query: str
) -> ToolResult:
    """Search Hevy exercise template IDs before creating/updating routines."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="search_hevy_exercises",
        args={"query": query},
        factory=lambda: create_search_hevy_exercises_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
    )


async def get_hevy_routine_detail(
    ctx: RunContext[ChatAgentDeps], routine_title_or_id: str
) -> ToolResult:
    """Read full Hevy routine details before any Hevy routine mutation."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="get_hevy_routine_detail",
        args={"routine_title_or_id": routine_title_or_id},
        factory=lambda: create_get_hevy_routine_detail_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
    )


async def create_hevy_routine(
    ctx: RunContext[ChatAgentDeps],
    title: str,
    exercises: list[dict],
    notes: str | None = None,
) -> ToolResult:
    """Create a Hevy routine after valid exercise template IDs are known."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="create_hevy_routine",
        args={"title": title, "exercises": exercises, "notes": notes},
        factory=lambda: create_create_hevy_routine_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


async def update_hevy_routine(
    ctx: RunContext[ChatAgentDeps],
    routine_title: str,
    new_title: str | None = None,
    exercises: list[dict] | None = None,
    notes: str | None = None,
    allow_structure_rebuild: bool = False,
) -> ToolResult:
    """Update a Hevy routine. Fetch full details first for structural changes."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="update_hevy_routine",
        args={
            "routine_title": routine_title,
            "new_title": new_title,
            "exercises": exercises,
            "notes": notes,
            "allow_structure_rebuild": allow_structure_rebuild,
        },
        factory=lambda: create_update_hevy_routine_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


async def replace_hevy_exercise(
    ctx: RunContext[ChatAgentDeps],
    routine_title: str,
    old_exercise_name_or_id: str,
    new_exercise_id: str,
) -> ToolResult:
    """Replace one exercise in a Hevy routine while preserving existing sets."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="replace_hevy_exercise",
        args={
            "routine_title": routine_title,
            "old_exercise_name_or_id": old_exercise_name_or_id,
            "new_exercise_id": new_exercise_id,
        },
        factory=lambda: create_replace_hevy_exercise_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


async def set_routine_rest_and_ranges(
    ctx: RunContext[ChatAgentDeps],
    routine_title_or_id: str,
    rest_seconds: int = 90,
    rep_range_start: int = 8,
    rep_range_end: int = 12,
) -> ToolResult:
    """Bulk update rest seconds and rep ranges in an existing Hevy routine."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="set_routine_rest_and_ranges",
        args={
            "routine_title_or_id": routine_title_or_id,
            "rest_seconds": rest_seconds,
            "rep_range_start": rep_range_start,
            "rep_range_end": rep_range_end,
        },
        factory=lambda: create_set_routine_rest_and_ranges_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )


async def trigger_hevy_import(
    ctx: RunContext[ChatAgentDeps], days_back: int = 7
) -> ToolResult:
    """Import recent workouts from Hevy into local history."""
    return await _legacy_async_result(
        ctx=ctx,
        tool_name="trigger_hevy_import",
        args={"days_back": days_back},
        factory=lambda: create_trigger_hevy_import_tool(
            ctx.deps.hevy_service, ctx.deps.database, ctx.deps.user_email
        ),
        saved=True,
        material_change=True,
    )
