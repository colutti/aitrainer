import pytest
from unittest.mock import MagicMock
from src.repositories.chat_repository import ChatRepository

@pytest.fixture
def chat_repository():
    return ChatRepository(database=MagicMock())

def test_get_history_pagination(chat_repository):
    """
    Test getting history with limit and offset (skip).
    """
    session_id = "test_pagination_user"
    
    # We will mock the internal functionality of get_history.
    # Since get_history currently relies on MongoDBChatMessageHistory,
    # and we want to CHANGE it to support pagination (likely via direct DB access),
    # we should mock the DB query.
    
    # BUT, if we keep using MongoDBChatMessageHistory, it might be hard to mock 'skip'.
    # So let's write the test assuming we WILL implement pagination.
    # We can mock the 'find' method on the collection if we switch implementation.
    
    # Let's assume we refactor get_history to use self.collection.find()
    
    # Setup mock collection
    mock_collection = MagicMock()
    chat_repository.collection = mock_collection
    
    # Create a list of mock documents simulating stored messages
    # Assuming MongoDBChatMessageHistory stores them in a way we can query individual messages?
    # Verification needed: Does it store 1 doc per message or 1 doc per session?
    # If it is 1 doc per session (default LangChain), pagination is HARD.
    # If it is 1 doc per message, pagination is EASY.
    
    # Looking at codebase_search result earlier, I saw "MongoDBChatMessageHistory(..., history_size=...)".
    # This suggests it supports history_size, but maybe relies on an index.
    
    # Let's assume for this test that the implementation will change to support pagination.
    # We will mock the return value of whatever method we call.
    
    # Actually, for TDD, let's define the interface we WANT.
    # get_history(user_id, limit=10, skip=10)
    
    # Prepare expected return
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    
    # Should resolve to a list of dicts/objects
    mock_cursor.to_list.return_value = [] # Async? No, repository is sync usually?
    # Repository methods seem synchronous in the snippet I saw (def get_history).
    # But BaseRepository usually might use Motor (async) or PyMongo (sync).
    # 'def get_history' (no async). So likely PyMongo.
    
    mock_collection.find.return_value = mock_cursor
    
    # Call the method
    # Note: We need to update the signature in the actual code first/simultaneously for valid python?
    # No, python allows kwargs or we can just pass them if we update the test to expect the new signature.
    
    # We will call with named args
    try:
        chat_repository.get_history(session_id, limit=5, offset=5)
    except TypeError:
        pytest.fail("get_history does not accept 'offset' argument yet")
    
    # Verify the chain of calls on the cursor
    # We expect: find({'SessionId': ...}).sort('timestamp', -1).skip(5).limit(5)
    # The actual sort key depends on DB schema.
    
    mock_collection.find.assert_called()
    mock_cursor.skip.assert_called_with(5)
    mock_cursor.limit.assert_called_with(5)
