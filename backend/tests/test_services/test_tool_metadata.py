from unittest.mock import MagicMock
from langchain_core.tools import BaseTool

from src.services.workout_tools import create_save_workout_tool, create_get_workouts_tool
from src.services.nutrition_tools import create_save_nutrition_tool, create_get_nutrition_tool
from src.services.composition_tools import create_save_composition_tool, create_get_composition_tool
from src.services.hevy_tools import (
    create_list_hevy_routines_tool,
    create_create_hevy_routine_tool,
    create_update_hevy_routine_tool,
    create_search_hevy_exercises_tool
)
from src.services.profile_tools import create_get_user_goal_tool, create_update_user_goal_tool

def test_tool_metadata_configuration():
    """
    Validation test to ensure tools are correctly marked as read (memory safe) 
    or write (memory unsafe).
    """
    mock_db = MagicMock()
    mock_hevy = MagicMock()
    user_email = "test@test.com"

    # --- WRITE TOOLS (Should have is_write_operation=True) ---
    write_tools = [
        create_save_workout_tool(mock_db, user_email),
        create_save_nutrition_tool(mock_db, user_email),
        create_save_composition_tool(mock_db, user_email),
        create_create_hevy_routine_tool(mock_hevy, mock_db, user_email),
        create_update_hevy_routine_tool(mock_hevy, mock_db, user_email),
        create_update_user_goal_tool(mock_db, user_email)
    ]

    for tool in write_tools:
        assert hasattr(tool, "extras"), f"Tool {tool.name} missing extras attribute"
        assert tool.extras is not None, f"Tool {tool.name} has None extras"
        assert tool.extras.get("is_write_operation") is True, \
            f"Tool {tool.name} should be marked as write operation"

    # --- READ TOOLS (Should NOT have is_write_operation=True) ---
    read_tools = [
        create_get_workouts_tool(mock_db, user_email),
        create_get_nutrition_tool(mock_db, user_email),
        create_get_composition_tool(mock_db, user_email),
        create_list_hevy_routines_tool(mock_hevy, mock_db, user_email),
        create_search_hevy_exercises_tool(mock_hevy, mock_db, user_email),
        create_get_user_goal_tool(mock_db, user_email)
    ]

    for tool in read_tools:
        # Extras might be None or empty, or simply not have the key
        is_write = False
        if hasattr(tool, "extras") and tool.extras:
            is_write = tool.extras.get("is_write_operation", False)
        
        assert is_write is False, \
            f"Tool {tool.name} should NOT be marked as write operation"
