"""
Tool registry with memory metadata for controlling Mem0 storage behavior.

Tools are classified as:
- EPHEMERAL: Read-only tools that fetch recoverable data (should NOT create memories)
- MEMORABLE: Write tools or actions that represent significant events (CAN create memories)
"""

from dataclasses import dataclass
from enum import Enum


class ToolMemoryType(Enum):
    """Classification for tool memory behavior."""

    EPHEMERAL = "ephemeral"  # Data is recoverable, skip Mem0
    MEMORABLE = "memorable"  # Event/action, allow Mem0


@dataclass
class ToolMetadata:
    """Metadata for a registered tool."""

    name: str
    memory_type: ToolMemoryType
    description: str


# Registry of tools and their memory classification
TOOL_REGISTRY: dict[str, ToolMetadata] = {
    # Ephemeral (GET - data in DB/API)
    "get_workouts": ToolMetadata(
        "get_workouts", ToolMemoryType.EPHEMERAL, "Fetch workouts"
    ),
    "get_nutrition": ToolMetadata(
        "get_nutrition", ToolMemoryType.EPHEMERAL, "Fetch nutrition"
    ),
    "get_body_composition": ToolMetadata(
        "get_body_composition", ToolMemoryType.EPHEMERAL, "Fetch weight"
    ),
    "get_user_goal": ToolMetadata(
        "get_user_goal", ToolMemoryType.EPHEMERAL, "Fetch goal"
    ),
    "list_hevy_routines": ToolMetadata(
        "list_hevy_routines", ToolMemoryType.EPHEMERAL, "List Hevy routines"
    ),
    "search_hevy_exercises": ToolMetadata(
        "search_hevy_exercises", ToolMemoryType.EPHEMERAL, "Search Hevy"
    ),
    "get_hevy_routine_detail": ToolMetadata(
        "get_hevy_routine_detail", ToolMemoryType.EPHEMERAL, "Fetch Hevy routine details"
    ),
    # Memorable (SAVE/CREATE/UPDATE - significant events)
    "save_workout": ToolMetadata(
        "save_workout", ToolMemoryType.MEMORABLE, "Save workout"
    ),
    "save_daily_nutrition": ToolMetadata(
        "save_daily_nutrition", ToolMemoryType.MEMORABLE, "Save nutrition"
    ),
    "save_body_composition": ToolMetadata(
        "save_body_composition", ToolMemoryType.MEMORABLE, "Save weight"
    ),
    "update_user_goal": ToolMetadata(
        "update_user_goal", ToolMemoryType.MEMORABLE, "Update goal"
    ),
    "create_hevy_routine": ToolMetadata(
        "create_hevy_routine", ToolMemoryType.MEMORABLE, "Create routine"
    ),
    "update_hevy_routine": ToolMetadata(
        "update_hevy_routine", ToolMemoryType.MEMORABLE, "Update routine"
    ),
    "replace_hevy_exercise": ToolMetadata(
        "replace_hevy_exercise", ToolMemoryType.MEMORABLE, "Replace exercise"
    ),
    "set_routine_rest_and_ranges": ToolMetadata(
        "set_routine_rest_and_ranges", ToolMemoryType.MEMORABLE, "Update rest times and rep ranges"
    ),
    # Memory management (AI-driven, replacing Mem0 extraction)
    "save_memory": ToolMetadata(
        "save_memory", ToolMemoryType.MEMORABLE, "Save memory"
    ),
    "search_memory": ToolMetadata(
        "search_memory", ToolMemoryType.EPHEMERAL, "Search memories"
    ),
    "list_raw_memories": ToolMetadata(
        "list_raw_memories", ToolMemoryType.EPHEMERAL, "List all memories for review"
    ),
    "update_memory": ToolMetadata(
        "update_memory", ToolMemoryType.MEMORABLE, "Update memory"
    ),
    "delete_memory": ToolMetadata(
        "delete_memory", ToolMemoryType.MEMORABLE, "Delete memory"
    ),
    "delete_memories_batch": ToolMetadata(
        "delete_memories_batch", ToolMemoryType.MEMORABLE, "Delete multiple memories"
    ),
    # Metabolism (adaptive TDEE and parameters)
    "get_metabolism_data": ToolMetadata(
        "get_metabolism_data", ToolMemoryType.EPHEMERAL, "Get adaptive TDEE data"
    ),
    "update_tdee_params": ToolMetadata(
        "update_tdee_params", ToolMemoryType.MEMORABLE, "Update TDEE parameters (activity_factor)"
    ),
}


def is_tool_ephemeral(tool_name: str) -> bool:
    """Check if a tool is classified as ephemeral (data is recoverable)."""
    metadata = TOOL_REGISTRY.get(tool_name)
    return metadata.memory_type == ToolMemoryType.EPHEMERAL if metadata else False


def should_store_memory(tools_called: list[str]) -> bool:
    """
    Determine if the conversation should be stored in Mem0.

    Rules:
    1. If NO tools were called -> Store (normal conversation may have preferences)
    2. If ONLY ephemeral tools -> Skip (just data retrieval)
    3. If ANY memorable tool -> Store (significant event happened)

    Args:
        tools_called: List of tool names that were invoked during the conversation.

    Returns:
        True if the conversation should be stored in Mem0.
    """
    if not tools_called:
        # No tools = normal conversation, may contain preferences
        return True

    has_memorable = any(not is_tool_ephemeral(tool) for tool in tools_called)

    return has_memorable
