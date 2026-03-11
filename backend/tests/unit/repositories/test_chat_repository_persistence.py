import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from src.repositories.chat_repository import ChatRepository
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.core.config import settings

@pytest.fixture
def chat_repository():
    return ChatRepository(database=MagicMock())

@pytest.fixture
def mock_mongo_history():
    with patch("src.repositories.chat_repository.MongoDBChatMessageHistory") as mock:
        yield mock

def test_add_message_persists_beyond_limit(chat_repository, mock_mongo_history):
    """
    Test that adding messages does not truncate history based on MAX_SHORT_TERM_MEMORY_MESSAGES.
    We want to ensure all messages are persisted.
    """
    session_id = "test_session_persistence"
    
    # Mock the MongoDBChatMessageHistory instance
    mock_history_instance = MagicMock()
    mock_mongo_history.return_value = mock_history_instance
    
    # Simulate adding 25 messages (MAX_SHORT_TERM_MEMORY_MESSAGES is 20)
    limit = settings.MAX_SHORT_TERM_MEMORY_MESSAGES
    messages_to_add = limit + 5
    
    for i in range(messages_to_add):
        chat_msg = ChatHistory(
            text=f"Message {i}",
            sender=Sender.STUDENT,
            timestamp=datetime.now().isoformat()
        )
        chat_repository.add_message(chat_msg, session_id)

    # Check how MongoDBChatMessageHistory was initialized
    # We expect 'history_size' to NOT be present or to be None/unlimited in the new implementation.
    # But for the RED phase (current buggy behavior), we expect it IS initialized with the limit.
    # To assert failure/success of the fix, we should check the initialization arguments.
    
    # In the current implementation (buggy), it initializes with history_size=20.
    # In the fixed implementation, it should NOT pass history_size (or pass None).
    
    # For this test to serve as a reproduction of the "unlimited persistence" requirement:
    # We verify that for EACH call, we are NOT passing a restrictive history_size.
    
    # Let's inspect the last call to constructor
    _, kwargs = mock_mongo_history.call_args
    
    # Assert that history_size is NOT responsible for truncation.
    # If history_size is passed as '20', this test should fail (conceptually) if we want unlimited.
    # However, since we are mocking, we can't check the DB count directly without a real DB.
    # So we assert on the CALL ARGUMENTS.
    
    # We WANT 'history_size' to be None or missing.
    assert "history_size" not in kwargs or kwargs["history_size"] is None, \
        f"MongoDBChatMessageHistory initialized with history_size limit: {kwargs.get('history_size')}"
