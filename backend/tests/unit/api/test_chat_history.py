"""
Tests for chat history model translation handling.
"""

from types import SimpleNamespace

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender


class FakeMessage:
    """Minimal message object for ChatHistory conversion tests."""

    def __init__(self, content: str, message_type: str, additional_kwargs=None):
        self.content = content
        self.type = message_type
        self.additional_kwargs = additional_kwargs


def test_from_mongodb_chat_message_history_preserves_translations() -> None:
    """Mongo chat history entries should keep per-locale translations."""
    history = SimpleNamespace(
        messages=[
            FakeMessage(
                content="Hello",
                message_type="human",
                additional_kwargs={
                    "timestamp": "2026-01-01T10:00:00Z",
                    "translations": {"pt-BR": "Olá"},
                },
            ),
            FakeMessage(
                content="Let's go.",
                message_type="ai",
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


def test_from_mongodb_chat_message_history_handles_missing_additional_kwargs() -> None:
    """Legacy imported messages without additional_kwargs should not crash conversion."""
    history = SimpleNamespace(
        messages=[
            FakeMessage(
                content="Mensagem antiga",
                message_type="human",
                additional_kwargs={},
            ),
            FakeMessage(
                content="Resposta antiga",
                message_type="ai",
                additional_kwargs={},
            ),
        ]
    )

    history.messages[0].additional_kwargs = None
    history.messages[1].additional_kwargs = None

    chat_history = ChatHistory.from_mongodb_chat_message_history(history)

    assert len(chat_history) == 2
    assert chat_history[0].sender == Sender.STUDENT
    assert chat_history[0].translations is None
    assert chat_history[0].timestamp == "0001-01-01T00:00:00"
    assert chat_history[1].sender == Sender.TRAINER
    assert chat_history[1].translations is None
