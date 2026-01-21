
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
from src.services.history_compactor import HistoryCompactor
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    # Mock stream_simple to return a generator of chunks
    async def async_gen(chunks):
        for c in chunks:
            yield c
            
    def sync_gen(prompt_template, input_data):
        yield "Updated Summary Content"
        
    client.stream_simple = MagicMock(side_effect=sync_gen)
    return client

@pytest.mark.asyncio
async def test_history_compactor_skips_short_history(mock_db, mock_llm_client):
    """Should not compact if history is within window."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)
    
    # Mock Profile - FULL FIELDS to satisfy Pydantic
    profile = UserProfile(
        email="test@test.com", 
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5
    )
    mock_db.get_user_profile.return_value = profile
    
    # Mock Short History (10 msgs)
    mock_db.get_chat_history.return_value = [MagicMock() for _ in range(10)]
    
    await compactor.compact_history("test@test.com", active_window_size=20)
    
    # Assertions
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.save_user_profile.assert_not_called()

@pytest.mark.asyncio
async def test_history_compactor_summarizes_old_messages(mock_db, mock_llm_client):
    """Should compact messages older than window."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)
    
    # Mock Profile
    profile = UserProfile(
        email="test@test.com", 
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5
    )
    mock_db.get_user_profile.return_value = profile
    
    # Mock Long History (30 msgs), Window (10) -> Compact 20
    # Create fake messages with timestamps
    base_ts = datetime(2026, 1, 1, 10, 0)
    messages = []
    for i in range(30):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT, 
            text=f"Msg {i}", 
            timestamp=ts.isoformat()
        )
        messages.append(msg)
        
    mock_db.get_chat_history.return_value = messages
    
    # Run
    await compactor.compact_history("test@test.com", active_window_size=10)
    
    # Assertions
    mock_llm_client.stream_simple.assert_called_once()
    mock_db.save_user_profile.assert_called_once()
    
    # Check if profile was updated
    updated_profile = mock_db.save_user_profile.call_args[0][0]
    assert updated_profile.long_term_summary == "Updated Summary Content"
    # The last compacted message should be index 19 (since 20-29 are active window)
    expected_ts = messages[19].timestamp
    assert updated_profile.last_compaction_timestamp == expected_ts

@pytest.mark.asyncio
async def test_history_compactor_idempotency(mock_db, mock_llm_client):
    """Should ignore messages already compacted (based on timestamp)."""
    compactor = HistoryCompactor(mock_db, mock_llm_client)
    
    # Last compaction was at Minute 19
    base_ts = datetime(2026, 1, 1, 10, 0)
    last_compacted_ts = (base_ts + timedelta(minutes=19)).isoformat()
    
    profile = UserProfile(
        email="test@test.com", 
        goal="test",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=175,
        goal_type="maintain",
        weekly_rate=0.5,
        last_compaction_timestamp=last_compacted_ts
    )
    mock_db.get_user_profile.return_value = profile
    
    # Same history as before
    messages = []
    for i in range(30):
        ts = base_ts + timedelta(minutes=i)
        msg = ChatHistory(
            sender=Sender.STUDENT, 
            text=f"Msg {i}", 
            timestamp=ts.isoformat()
        )
        messages.append(msg)
    mock_db.get_chat_history.return_value = messages

    # Run with same window
    await compactor.compact_history("test@test.com", active_window_size=10)
    
    # Since all "old" messages (0-19) are <= last_compaction_timestamp, 
    # NO NEW lines to summarize.
    mock_llm_client.stream_simple.assert_not_called()
    mock_db.save_user_profile.assert_not_called()
