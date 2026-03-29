"""
Tests for chat history model translation handling.
"""

from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender


def test_from_mongodb_chat_message_history_preserves_translations() -> None:
    """Mongo chat history entries should keep per-locale translations."""
    history = SimpleNamespace(
        messages=[
            HumanMessage(
                content="Hello",
                additional_kwargs={
                    "timestamp": "2026-01-01T10:00:00Z",
                    "translations": {"pt-BR": "Olá"},
                },
            ),
            AIMessage(
                content="Let's go.",
                additional_kwargs={
                    "timestamp": "2026-01-01T10:01:00Z",
                    "trainer_type": "gymbro",
                    "translations": {"pt-BR": "Bora."},
                },
            ),
        ]
    )

    chat_history = ChatHistory.from_mongodb_chat_message_history(history)

    assert len(chat_history) == 2
    assert chat_history[0].sender == Sender.STUDENT
    assert chat_history[0].translations == {"pt-BR": "Olá"}
    assert chat_history[1].sender == Sender.TRAINER
    assert chat_history[1].translations == {"pt-BR": "Bora."}
