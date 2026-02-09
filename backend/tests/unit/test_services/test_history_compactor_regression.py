import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.services.history_compactor import HistoryCompactor
from src.api.models.chat_history import ChatHistory, Sender
from src.api.models.user_profile import UserProfile

@pytest.mark.asyncio
async def test_compaction_candidates_availability_regression():
    """
    CRITICAL REGRESSION TEST:
    Ensures that the chat repository returns enough messages to trigger compaction.
    If the repository truncates history (e.g. at 20 messages) like the bug we found,
    this test failed because candidates were empty.
    
    This specific test verifies the logic of the compactor assuming the repository behaves correctly.
    (See test_chat_repository_persistence.py for the repository fix verification).
    """
    # 1. Setup - Mock Dependencies
    mock_db = MagicMock()
    mock_db.update_user_profile_fields.return_value = True
    
    mock_llm_client = MagicMock()
    
    # Mock LLM stream
    async def async_gen(*args, **kwargs):
        yield '{"preferences": ["updated"]}'
    mock_llm_client.stream_simple = MagicMock(side_effect=async_gen)
    
    compactor = HistoryCompactor(mock_db, mock_llm_client)

    # Mock Profile
    profile = UserProfile(
        email="regression@test.com",
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    mock_db.get_user_profile.return_value = profile

    # 2. Simulate 30 VALID messages in DB
    # Must be > 10 chars to pass _preprocess_messages filter
    total_messages = 30
    active_window = 20
    
    messages = []
    base_ts = datetime(2026, 1, 1, 10, 0)
    for i in range(total_messages):
        ts = base_ts + timedelta(minutes=i)
        # Content must be relevant and > 10 chars
        content = f"Message content specific regression test {i}"
        messages.append(ChatHistory(
            sender=Sender.STUDENT, 
            text=content, 
            timestamp=ts.isoformat()
        ))
    
    mock_db.get_chat_history.return_value = messages

    # 3. Run Compaction
    # active_window=20 means last 20 are "window". 
    # candidates = messages[:-20] -> First 10 messages (0..9).
    await compactor.compact_history(
        "regression@test.com", 
        active_window_size=active_window, 
        compaction_threshold=25 # Threshold < 30 triggers compaction
    )

    # 4. Assertions
    # Verify LLM called (implies candidates were found)
    mock_llm_client.stream_simple.assert_called_once()
    
    # Verify correct candidates were processed
    call_kwargs = mock_llm_client.stream_simple.call_args[1]
    input_data = call_kwargs["input_data"]
    new_lines = input_data["new_lines"]
    
    # Check that message 0 is present and message 20 is NOT present
    # "Message content specific regression test 0"
    assert "Message content specific regression test 0" in new_lines
    assert "Message content specific regression test 9" in new_lines
    assert "Message content specific regression test 10" not in new_lines # Msg 10 starts the window
