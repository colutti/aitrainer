import pytest
from unittest.mock import MagicMock, patch
from src.repositories.chat_repository import ChatRepository

@pytest.fixture
def chat_repository():
    return ChatRepository(database=MagicMock())

@patch("src.repositories.chat_repository.messages_from_dict")
@patch("src.api.models.chat_history.ChatHistory.from_mongodb_chat_message_history")
def test_get_history_pagination(mock_from_mongo, mock_messages_from_dict, chat_repository):
    """
    Test getting history with limit and offset (skip).
    """
    session_id = "test_pagination_user"
    limit = 5
    offset = 5
    
    # Create mock messages
    mock_messages = [MagicMock(sender="Student") for _ in range(limit + offset + 5)]
    mock_from_mongo.return_value = mock_messages
    
    # Mock collection.find
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = []
    mock_find_cursor = MagicMock()
    mock_find_cursor.sort.return_value = mock_find_cursor
    mock_find_cursor.skip.return_value = mock_find_cursor
    mock_find_cursor.limit.return_value = mock_cursor
    chat_repository.collection.find.return_value = mock_find_cursor

    # Call the method
    result = chat_repository.get_history(session_id, limit=limit, offset=offset)
    
    # Verify manual pagination (slicing)
    # With 15 messages total, offset 5 from end: 15..11 are skipped. 10..6 are taken.
    assert len(result) == 5


def test_get_history_uses_desc_cursor_window(chat_repository):
    """Should query newest entries first with skip/limit windowing."""
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = []
    mock_find_cursor = MagicMock()
    mock_find_cursor.sort.return_value = mock_find_cursor
    mock_find_cursor.skip.return_value = mock_find_cursor
    mock_find_cursor.limit.return_value = mock_cursor
    chat_repository.collection.find.return_value = mock_find_cursor

    with patch("src.repositories.chat_repository.ChatHistory.from_mongodb_chat_message_history", return_value=[]):
        chat_repository.get_history("abc", limit=20, offset=40)

    mock_find_cursor.sort.assert_called_with("_id", -1)
    mock_find_cursor.skip.assert_called()
    mock_find_cursor.limit.assert_called()
