"""
Tests for AI Trainer streaming and error handling in src/services/trainer.py
"""

import pytest
from unittest.mock import MagicMock, patch
from src.services.trainer import AITrainerBrain
from langchain_core.messages import HumanMessage


@pytest.fixture
def mock_deps():
    db = MagicMock()
    llm = MagicMock()
    memory = MagicMock()
    return db, llm, memory


@pytest.mark.asyncio
async def test_send_message_ai_streaming_error(mock_deps):
    """Test streaming response when an error occurs mid-stream."""
    db, llm, memory = mock_deps

    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm)

    # Mock user and trainer profiles
    db.get_user_profile.return_value = MagicMock(
        get_profile_summary=lambda: "User Summary",
        current_billing_cycle_start=None,
        subscription_plan="Free",
        total_messages_sent=0,
        custom_message_limit=None
    )
    db.get_trainer_profile.return_value = MagicMock(
        trainer_type="atlas", get_trainer_profile_summary=lambda: "Trainer Summary"
    )

    # Mock conversation memory and variables
    mock_memory_obj = MagicMock()
    mock_memory_obj.load_memory_variables.return_value = {"chat_history": []}
    db.get_window_memory.return_value = mock_memory_obj

    # Mock stream to fail after first chunk
    async def error_stream(**kwargs):
        yield "First chunk"
        raise Exception("Stream failed")

    llm.stream_with_tools.side_effect = error_stream

    # Execute generator
    gen = trainer.send_message_ai("user@test.com", "Hello")

    first = await anext(gen)
    assert first == "First chunk"
    
    with pytest.raises(Exception, match="Stream failed"):
        await anext(gen)


def test_get_memories_paginated_error(mock_deps):
    """Test get_memories_paginated handling Qdrant error."""
    db, llm, memory = mock_deps
    db, llm, memory = mock_deps
    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm)

    mock_qdrant = MagicMock()
    mock_qdrant.count.side_effect = Exception("Qdrant unavailable")

    with pytest.raises(Exception, match="Qdrant unavailable"):
        trainer.get_memories_paginated(
            "user@test.com", 1, 10, mock_qdrant, "test_collection"
        )


def test_get_memory_by_id_error(mock_deps):
    """Test get_memory_by_id handling error gracefully."""
    db, llm, memory = mock_deps
    qdrant_client = MagicMock()
    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm, qdrant_client)

    qdrant_client.retrieve.side_effect = Exception("Not found")

    result = trainer.get_memory_by_id("mem_id", "test@example.com")
    assert result is None


def test_format_memory_messages_unknown_type(mock_deps):
    """Test _format_memory_messages with unknown message type."""
    db, llm, memory = mock_deps
    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm)

    class UnknownMessage:
        content = "Unknown content"
        type = "unknown"

    msg = UnknownMessage()
    result = trainer._format_history_as_messages([msg], "atlas")

    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert "Unknown content" in result[0].content
