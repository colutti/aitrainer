"""
Canonical node tool exposure policy.

Single source of truth for which tools each graph node may use,
how they are exposed (LLM direct vs orchestrator-only), and what
exposure class each tool belongs to.

Any drift between this policy, runtime allowed_tools, node JSON
tool_names, prompt references, or the global tool registry MUST be
detected by structural tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class ExposureClass(Enum):
    """Whether a tool is safe to expose in conversational nodes."""

    CONVERSATIONAL = "conversational"
    OPERATIONAL_RAW = "operational_raw"
    ADMIN_OR_MAINTENANCE = "admin_or_maintenance"
    DEPRECATED = "deprecated"


class ExposureMode(Enum):
    """How a tool is handed to a node at runtime."""

    LLM_DIRECT = "llm_direct"
    ORCHESTRATOR_ONLY = "orchestrator_only"
    NON_CONVERSATIONAL = "non_conversational"


@dataclass(frozen=True)
class ToolPolicy:
    """Per-tool classification and exposure metadata."""

    name: str
    domain: str
    exposure_class: ExposureClass
    exposure_mode: ExposureMode
    description: str
    replaces: str | None = None
    replaced_by: str | None = None


_NODE_POLICY: dict[str, dict[str, FrozenSet[str]]] = {
    "session_context": {
        "llm_direct": frozenset(),
        "orchestrator_only": frozenset(),
    },
    "prompt_security": {
        "llm_direct": frozenset(),
        "orchestrator_only": frozenset(),
    },
    "training_specialist": {
        "llm_direct": frozenset({
            "save_workout",
            "get_workouts",
            "list_hevy_routines",
            "get_hevy_routine_detail",
            "trigger_hevy_import",
            "create_hevy_routine",
            "update_hevy_routine",
            "search_hevy_exercises",
            "replace_hevy_exercise",
            "set_routine_rest_and_ranges",
            "save_body_composition",
            "get_body_composition",
        }),
        "orchestrator_only": frozenset(),
    },
    "nutrition_specialist": {
        "llm_direct": frozenset({
            "save_daily_nutrition",
            "get_nutrition",
            "sync_nutrition_text",
            "get_workouts",
            "get_metabolism_data",
            "get_user_goal",
            "update_tdee_params",
        }),
        "orchestrator_only": frozenset(),
    },
    "plan_specialist": {
        "llm_direct": frozenset({
            "get_plan",
            "upsert_plan",
            "plan_help",
            "get_user_goal",
            "update_user_goal",
            "get_metabolism_data",
        }),
        "orchestrator_only": frozenset(),
    },
    "coach_reply": {
        "llm_direct": frozenset(),
        "orchestrator_only": frozenset(),
    },
    "memory_hub": {
        "llm_direct": frozenset(),
        "orchestrator_only": frozenset({
            "list_events",
            "create_event",
            "update_event",
            "delete_event",
            "search_memory",
            "save_memory",
            "update_memory",
            "delete_memory",
        }),
    },
}


TOOL_EXPOSURE_POLICY: dict[str, ToolPolicy] = {
    "save_workout": ToolPolicy(
        name="save_workout",
        domain="workout",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Save a completed workout session",
    ),
    "get_workouts": ToolPolicy(
        name="get_workouts",
        domain="workout",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch recent workout history",
    ),
    "get_workouts_raw": ToolPolicy(
        name="get_workouts_raw",
        domain="workout",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Raw paginated workout data for audit/debug",
    ),
    "save_daily_nutrition": ToolPolicy(
        name="save_daily_nutrition",
        domain="nutrition",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Save daily nutrition log",
    ),
    "get_nutrition": ToolPolicy(
        name="get_nutrition",
        domain="nutrition",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch recent nutrition history",
    ),
    "get_nutrition_raw": ToolPolicy(
        name="get_nutrition_raw",
        domain="nutrition",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Raw paginated nutrition data for audit/debug",
    ),
    "sync_nutrition_text": ToolPolicy(
        name="sync_nutrition_text",
        domain="nutrition",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Parse and extract macros from free-text nutrition input",
    ),
    "save_body_composition": ToolPolicy(
        name="save_body_composition",
        domain="body_composition",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Save body composition measurements",
    ),
    "get_body_composition": ToolPolicy(
        name="get_body_composition",
        domain="body_composition",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch recent body composition history",
    ),
    "get_body_composition_raw": ToolPolicy(
        name="get_body_composition_raw",
        domain="body_composition",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Raw paginated body composition data for audit/debug",
    ),
    "list_hevy_routines": ToolPolicy(
        name="list_hevy_routines",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="List Hevy workout routines",
    ),
    "get_hevy_routine_detail": ToolPolicy(
        name="get_hevy_routine_detail",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch Hevy routine details",
    ),
    "trigger_hevy_import": ToolPolicy(
        name="trigger_hevy_import",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Import workouts from Hevy",
    ),
    "create_hevy_routine": ToolPolicy(
        name="create_hevy_routine",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Create a new Hevy routine",
    ),
    "update_hevy_routine": ToolPolicy(
        name="update_hevy_routine",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Update an existing Hevy routine",
    ),
    "search_hevy_exercises": ToolPolicy(
        name="search_hevy_exercises",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Search Hevy exercise catalog",
    ),
    "replace_hevy_exercise": ToolPolicy(
        name="replace_hevy_exercise",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Replace an exercise in a Hevy routine",
    ),
    "set_routine_rest_and_ranges": ToolPolicy(
        name="set_routine_rest_and_ranges",
        domain="hevy",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Set rest times and rep ranges on a Hevy routine",
    ),
    "get_user_goal": ToolPolicy(
        name="get_user_goal",
        domain="goals",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch current user goal",
    ),
    "update_user_goal": ToolPolicy(
        name="update_user_goal",
        domain="goals",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Update user goal settings",
    ),
    "get_goal_history_raw": ToolPolicy(
        name="get_goal_history_raw",
        domain="goals",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Raw goal history snapshots for audit",
    ),
    "get_metabolism_data": ToolPolicy(
        name="get_metabolism_data",
        domain="metabolism",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch adaptive TDEE and metabolism data",
    ),
    "update_tdee_params": ToolPolicy(
        name="update_tdee_params",
        domain="metabolism",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Update TDEE activity factor and optionally reset tracking",
        replaces="reset_tdee_tracking",
    ),
    "reset_tdee_tracking": ToolPolicy(
        name="reset_tdee_tracking",
        domain="metabolism",
        exposure_class=ExposureClass.DEPRECATED,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Reset TDEE tracking history",
        replaced_by="update_tdee_params",
    ),
    "get_plan": ToolPolicy(
        name="get_plan",
        domain="plan",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Fetch the user's active plan",
    ),
    "upsert_plan": ToolPolicy(
        name="upsert_plan",
        domain="plan",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Create or update the user's plan",
    ),
    "plan_help": ToolPolicy(
        name="plan_help",
        domain="plan",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.LLM_DIRECT,
        description="Get plan creation/update instructions",
    ),
    "search_memory": ToolPolicy(
        name="search_memory",
        domain="memory",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Search user memories",
    ),
    "save_memory": ToolPolicy(
        name="save_memory",
        domain="memory",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Persist a new memory",
    ),
    "update_memory": ToolPolicy(
        name="update_memory",
        domain="memory",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Update an existing memory",
    ),
    "delete_memory": ToolPolicy(
        name="delete_memory",
        domain="memory",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Delete a memory",
    ),
    "list_raw_memories": ToolPolicy(
        name="list_raw_memories",
        domain="memory",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="List all raw memories for review",
    ),
    "get_memories_raw": ToolPolicy(
        name="get_memories_raw",
        domain="memory",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Fetch raw memory data for audit",
    ),
    "delete_memories_batch": ToolPolicy(
        name="delete_memories_batch",
        domain="memory",
        exposure_class=ExposureClass.ADMIN_OR_MAINTENANCE,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Batch delete multiple memories",
    ),
    "list_events": ToolPolicy(
        name="list_events",
        domain="events",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="List active events",
    ),
    "create_event": ToolPolicy(
        name="create_event",
        domain="events",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Create a scheduled event",
    ),
    "update_event": ToolPolicy(
        name="update_event",
        domain="events",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Update a scheduled event",
    ),
    "delete_event": ToolPolicy(
        name="delete_event",
        domain="events",
        exposure_class=ExposureClass.CONVERSATIONAL,
        exposure_mode=ExposureMode.ORCHESTRATOR_ONLY,
        description="Delete a scheduled event",
    ),
    "get_events_raw": ToolPolicy(
        name="get_events_raw",
        domain="events",
        exposure_class=ExposureClass.OPERATIONAL_RAW,
        exposure_mode=ExposureMode.NON_CONVERSATIONAL,
        description="Raw paginated events data for audit/debug",
    ),
}


def get_node_llm_tools(node_name: str) -> set[str]:
    """Return the set of tools a node may use via LLM tool calling."""
    policy = _NODE_POLICY.get(node_name, {})
    return set(policy.get("llm_direct", frozenset()))


def get_node_orchestrator_tools(node_name: str) -> set[str]:
    """Return tools that a node's orchestrator logic may access directly."""
    policy = _NODE_POLICY.get(node_name, {})
    return set(policy.get("orchestrator_only", frozenset()))


def get_node_all_tools(node_name: str) -> set[str]:
    """Return all tools (LLM + orchestrator) that a node may use."""
    return get_node_llm_tools(node_name) | get_node_orchestrator_tools(node_name)


def is_conversational_tool(tool_name: str) -> bool:
    """Check whether a tool is approved for conversational node exposure."""
    tp = TOOL_EXPOSURE_POLICY.get(tool_name)
    return tp is not None and tp.exposure_class == ExposureClass.CONVERSATIONAL


def is_deprecated_tool(tool_name: str) -> bool:
    """Check whether a tool is deprecated."""
    tp = TOOL_EXPOSURE_POLICY.get(tool_name)
    return tp is not None and tp.exposure_class == ExposureClass.DEPRECATED


_ALL_NODE_NAMES = frozenset(_NODE_POLICY.keys())


def all_known_node_names() -> frozenset[str]:
    """Return the set of node names governed by this policy."""
    return _ALL_NODE_NAMES


_ALL_TOOL_NAMES = frozenset(TOOL_EXPOSURE_POLICY.keys())


def all_known_tool_names() -> frozenset[str]:
    """Return the set of tool names classified by this policy."""
    return _ALL_TOOL_NAMES
