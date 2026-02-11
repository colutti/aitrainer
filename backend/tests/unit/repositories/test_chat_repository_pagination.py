import pytest
from unittest.mock import MagicMock, patch
from src.repositories.chat_repository import ChatRepository

@pytest.fixture
def chat_repository():
    return ChatRepository(database=MagicMock())

@patch("src.repositories.chat_repository.MongoDBChatMessageHistory")
@patch("src.api.models.chat_history.ChatHistory.from_mongodb_chat_message_history")
def test_get_history_pagination(mock_from_mongo, mock_mongo_history, chat_repository):
    """
    Test getting history with limit and offset (skip).
    """
    session_id = "test_pagination_user"
    limit = 5
    offset = 5
    
    # Create mock messages
    mock_messages = [MagicMock() for _ in range(limit + offset)]
    mock_from_mongo.return_value = mock_messages
    
    # Call the method
    result = chat_repository.get_history(session_id, limit=limit, offset=offset)
    
    # Verify MongoDBChatMessageHistory was called with correct history_size (limit + offset)
    mock_mongo_history.assert_called_once()
    args, kwargs = mock_mongo_history.call_args
    assert kwargs["history_size"] == limit + offset
    assert kwargs["session_id"] == session_id
    
    # Verify manual pagination (slicing)
    # With limit=5, offset=5, it fetches 10, drops last 5, takes last 5.
    # Expected result should be mock_messages[:5]
    assert result == mock_messages[:5]
    assert len(result) == 5
