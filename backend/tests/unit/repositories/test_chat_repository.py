"""Tests for chat repository history storage and decoding."""

from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.chat_repository import ChatRepository


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def chat_repo(mock_db):
    """Create ChatRepository instance with mock database."""
    return ChatRepository(mock_db)


def _cursor_with_docs(docs: list[dict]) -> MagicMock:
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.limit.return_value = docs
    return cursor


def _find_once(chat_repo, docs: list[dict]) -> None:
    chat_repo.collection.find.side_effect = [_cursor_with_docs(docs), _cursor_with_docs([])]


def test_get_history_decodes_new_documents(chat_repo):
    """Repository should read the new plain document format."""
    _find_once(
        chat_repo,
        [
            {
                "_id": 2,
                "History": {
                    "sender": "trainer",
                    "text": "Resposta",
                    "timestamp": "2026-01-01T10:01:00",
                    "trainer_type": "atlas",
                    "translations": {"en-US": "Answer"},
                },
            },
            {
                "_id": 1,
                "History": {
                    "sender": "student",
                    "text": "Oi",
                    "timestamp": "2026-01-01T10:00:00",
                },
            },
        ],
    )

    result = chat_repo.get_history("user@test.com", limit=20)

    assert [message.text for message in result] == ["Oi", "Resposta"]
    assert result[0].sender == Sender.STUDENT
    assert result[1].sender == Sender.TRAINER
    assert result[1].trainer_type == "atlas"
    assert result[1].translations == {"en-US": "Answer"}


def test_get_history_decodes_legacy_json_documents(chat_repo):
    """Legacy JSON rows remain readable during migration."""
    _find_once(
        chat_repo,
        [
            {
                "_id": 2,
                "History": json.dumps(
                    {
                        "type": "ai",
                        "data": {
                            "content": "Legacy reply",
                            "additional_kwargs": {
                                "timestamp": "2026-01-01T10:01:00",
                                "trainer_type": "gymbro",
                            },
                        },
                    }
                ),
            },
            {
                "_id": 1,
                "History": json.dumps(
                    {
                        "type": "human",
                        "data": {
                            "content": "Legacy user",
                            "additional_kwargs": {
                                "timestamp": "2026-01-01T10:00:00"
                            },
                        },
                    }
                ),
            },
        ],
    )

    result = chat_repo.get_history("user@test.com", limit=20)

    assert [message.text for message in result] == ["Legacy user", "Legacy reply"]
    assert result[1].trainer_type == "gymbro"


def test_add_messages_persists_conversation_in_one_batch(chat_repo):
    """A user/assistant pair should require one MongoDB write round trip."""
    now = datetime.now().isoformat()
    messages = [
        ChatHistory(text="Atualiza o plano", sender=Sender.STUDENT, timestamp=now),
        ChatHistory(text="Plano atualizado", sender=Sender.TRAINER, timestamp=now),
    ]

    chat_repo.add_messages(messages, "session_123", trainer_type="atlas")

    chat_repo.collection.insert_many.assert_called_once()
    documents = chat_repo.collection.insert_many.call_args.args[0]
    assert [document["SessionId"] for document in documents] == [
        "session_123",
        "session_123",
    ]
    assert documents[0]["History"]["sender"] == "Student"
    assert documents[0]["History"]["text"] == "Atualiza o plano"
    assert documents[1]["History"]["sender"] == "Trainer"
    assert documents[1]["History"]["trainer_type"] == "atlas"


def test_get_window_memory_returns_compatibility_wrapper(chat_repo):
    """Compatibility wrapper should expose load_memory_variables."""
    chat_repo.collection.find.return_value = _cursor_with_docs([])

    memory = chat_repo.get_window_memory("session_123", k=10)

    assert memory.load_memory_variables({}) == {"chat_history": []}


def test_get_pydantic_ai_history_converts_public_messages(chat_repo):
    """Recent public history should become Pydantic AI model messages."""
    now = "2026-01-01T10:00:00"
    _find_once(
        chat_repo,
        [
            {
                "_id": 2,
                "History": {
                    "sender": "trainer",
                    "text": "Resposta",
                    "timestamp": now,
                    "trainer_type": "atlas",
                },
            },
            {
                "_id": 1,
                "History": {
                    "sender": "student",
                    "text": "Oi",
                    "timestamp": now,
                },
            },
        ],
    )

    history = chat_repo.get_pydantic_ai_history("session_123", limit=10)

    assert isinstance(history[0], ModelRequest)
    assert isinstance(history[1], ModelResponse)
