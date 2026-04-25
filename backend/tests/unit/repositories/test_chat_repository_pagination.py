import pytest
from unittest.mock import MagicMock, patch
from src.repositories.chat_repository import ChatRepository

@pytest.fixture
def chat_repository():
    return ChatRepository(database=MagicMock())

def test_get_history_pagination(chat_repository):
    """
    Test getting history with limit and offset (skip).
    """
    session_id = "test_pagination_user"
    limit = 5
    offset = 5
    
    # Mock collection.find (15 public human messages, newest->oldest)
    docs = [
        {"_id": 100 - i, "History": '{"type":"human","data":{"content":"m","additional_kwargs":{"timestamp":"2026-01-01T00:00:00"}}}'}
        for i in range(limit + offset + 5)
    ]
    mock_find_cursor = MagicMock()
    mock_find_cursor.sort.return_value = mock_find_cursor
    mock_find_cursor.limit.return_value = docs
    chat_repository.collection.find.return_value = mock_find_cursor

    # Call the method
    result = chat_repository.get_history(session_id, limit=limit, offset=offset)
    
    # Verify manual pagination (slicing)
    # With 15 messages total, offset 5 from end: 15..11 are skipped. 10..6 are taken.
    assert len(result) == 5


def test_get_history_uses_desc_cursor_window(chat_repository):
    """Should query newest entries first with descending _id pagination."""
    mock_cursor_first = [{"_id": 30, "History": "{}"}]
    mock_cursor_second = []
    mock_find_cursor = MagicMock()
    mock_find_cursor.sort.return_value = mock_find_cursor
    mock_find_cursor.limit.side_effect = [mock_cursor_first, mock_cursor_second]
    chat_repository.collection.find.return_value = mock_find_cursor

    with patch("src.repositories.chat_repository.ChatHistory.from_mongodb_chat_message_history", return_value=[]):
        chat_repository.get_history("abc", limit=20, offset=40)

    mock_find_cursor.sort.assert_called_with("_id", -1)
    mock_find_cursor.limit.assert_called()
    first_call = chat_repository.collection.find.call_args_list[0]
    second_call = chat_repository.collection.find.call_args_list[1]
    assert first_call.args[0] == {"SessionId": "abc"}
    assert first_call.args[1] == {"History": 1}
    assert second_call.args[0] == {"SessionId": "abc", "_id": {"$lt": 30}}
