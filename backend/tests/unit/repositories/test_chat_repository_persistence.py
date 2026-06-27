"""Persistence tests for chat repository."""

from datetime import datetime
from unittest.mock import MagicMock

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.core.config import settings
from src.repositories.chat_repository import ChatRepository


def test_add_message_persists_beyond_short_term_memory_limit():
    """Adding messages should not truncate storage at the prompt window limit."""
    repository = ChatRepository(database=MagicMock())
    session_id = "test_session_persistence"

    limit = settings.MAX_SHORT_TERM_MEMORY_MESSAGES
    for i in range(limit + 5):
        repository.add_message(
            ChatHistory(
                text=f"Message {i}",
                sender=Sender.STUDENT,
                timestamp=datetime.now().isoformat(),
            ),
            session_id,
        )

    assert repository.collection.insert_many.call_count == limit + 5
    first_doc = repository.collection.insert_many.call_args_list[0].args[0][0]
    assert first_doc["SessionId"] == session_id
    assert first_doc["History"]["sender"] == "Student"
