from unittest.mock import MagicMock, AsyncMock, patch
import pytest
from src.services.trainer import AITrainerBrain
from langchain_core.messages import AIMessage
from langchain_core.tools import tool

# Definir ferramentas mockadas com e sem metadata
@tool(extras={"is_write_operation": True})
def mock_write_tool(arg: str):
    """Write tool"""
    return "write"

@tool
def mock_read_tool(arg: str):
    """Read tool"""
    return "read"

@pytest.fixture
def mock_deps():
    db = MagicMock()
    llm = MagicMock()
    memory = MagicMock()
    return db, llm, memory

@pytest.fixture
def trainer(mock_deps):
    db, llm, memory = mock_deps
    # Mock create tools methods to return our mocks
    with patch("src.services.trainer.create_save_workout_tool", return_value=mock_write_tool), \
         patch("src.services.trainer.create_get_workouts_tool", return_value=mock_read_tool), \
         patch("src.services.trainer.create_save_nutrition_tool", return_value=mock_write_tool), \
         patch("src.services.trainer.create_get_nutrition_tool", return_value=mock_read_tool), \
         patch("src.services.trainer.create_save_composition_tool", return_value=mock_write_tool), \
         patch("src.services.trainer.create_get_composition_tool", return_value=mock_read_tool), \
         patch("src.services.hevy_tools.create_list_hevy_routines_tool", return_value=mock_read_tool), \
         patch("src.services.hevy_tools.create_create_hevy_routine_tool", return_value=mock_write_tool), \
         patch("src.services.hevy_tools.create_update_hevy_routine_tool", return_value=mock_write_tool), \
         patch("src.services.hevy_tools.create_search_hevy_exercises_tool", return_value=mock_read_tool), \
         patch("src.services.profile_tools.create_get_user_goal_tool", return_value=mock_read_tool), \
         patch("src.services.profile_tools.create_update_user_goal_tool", return_value=mock_write_tool):
        
        brain = AITrainerBrain(db, llm, memory)
        
        # Configure internal mocks to avoid Pydantic validation errors
        mock_trainer_profile = MagicMock()
        mock_trainer_profile.trainer_type = "atlas"
        mock_trainer_profile.get_trainer_profile_summary.return_value = "Summary"
        
        mock_user_profile = MagicMock()
        mock_user_profile.get_profile_summary.return_value = "User Summary"
        
        brain._get_or_create_trainer_profile = MagicMock(return_value=mock_trainer_profile)
        brain._get_or_create_user_profile = MagicMock(return_value=mock_user_profile)
        
        return brain

def test_read_tool_allows_memory(trainer, mock_deps):
    """Test that calling a read tool DOES NOT block memory generation"""
    _, llm_client, _ = mock_deps
    
    # Configure LLM client to yield a read tool call
    # Yields: content, final_signal
    # For stream_with_tools, it yields content strings, then ("", write_tool_was_called)
    def mock_stream(*args, **kwargs):
        # Simulate tool usage logic internally if we were testing llm_client directly,
        # but here we are mocking llm_client.stream_with_tools response.
        # Ideally we should integration test llm_client -> trainer, but mocking stream is faster.
        # Wait, trainer uses llm_client.stream_with_tools. We need to mock that method.
        pass

    # Better approach: Test llm_client logic separately or integration
    # Let's test the flow in Trainer.send_message_ai by mocking llm_client.stream_with_tools return values
    
    # Scenario: Read tool called
    # output chunks... then ("", False) -> False means NO write tool called
    llm_client.stream_with_tools.return_value = iter([
        "Thinking...", 
        ("", False) # write_tool_was_called = False
    ])
    
    background_tasks = MagicMock()
    
    # Execute
    gen = trainer.send_message_ai("user@test.com", "list workouts", background_tasks)
    list(gen) # Consume generator
    
    # Verify memory task WAS scheduled
    # trainer.py: 
    # if not write_tool_was_called: background_tasks.add_task(...)
    assert background_tasks.add_task.called, "Memory generation should be scheduled for read tools"
    
    # Verify the task added was _add_to_mem0_background
    task_func = background_tasks.add_task.call_args[0][0]
    assert task_func.__name__ == "_add_to_mem0_background"


def test_write_tool_blocks_memory(trainer, mock_deps):
    """Test that calling a write tool BLOCKS memory generation"""
    _, llm_client, _ = mock_deps
    
    # Scenario: Write tool called
    # output chunks... then ("", True) -> True means write tool WAS called
    llm_client.stream_with_tools.return_value = iter([
        "Saving...", 
        ("", True) # write_tool_was_called = True
    ])
    
    background_tasks = MagicMock()
    
    # Execute
    gen = trainer.send_message_ai("user@test.com", "save workout", background_tasks)
    list(gen) # Consume generator
    
    # Verify memory task was NOT scheduled
    assert not background_tasks.add_task.called, "Memory generation should be skipped for write tools"
