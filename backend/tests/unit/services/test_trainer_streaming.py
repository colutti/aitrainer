"""
Tests for AI Trainer streaming and error handling in src/services/trainer.py
"""

import pytest
from unittest.mock import MagicMock
from src.services.trainer import AITrainerBrain
from langchain_core.messages import HumanMessage


@pytest.fixture
def mock_deps():
    db = MagicMock()
    llm = MagicMock()
    memory = MagicMock()
    return db, llm, memory





@pytest.mark.asyncio
async def test_get_memories_paginated_error(mock_deps):

    """Test get_memories_paginated handling Qdrant error."""
    db, llm, memory = mock_deps
    db, llm, memory = mock_deps
    mock_qdrant = MagicMock()
    trainer = AITrainerBrain(db, llm, qdrant_client=mock_qdrant)

    mock_qdrant.count.side_effect = Exception("Qdrant unavailable")



    with pytest.raises(Exception, match="Qdrant unavailable"):
        await trainer.get_memories_paginated(
            "user@test.com", 1, 10
        )


def test_get_memory_by_id_error(mock_deps):
    """Test get_memory_by_id handling error gracefully."""
    db, llm, memory = mock_deps
    qdrant_client = MagicMock()
    trainer = AITrainerBrain(db, llm, qdrant_client)

    qdrant_client.retrieve.side_effect = Exception("Not found")

    result = trainer.get_memory_by_id("mem_id")
    assert result is None


def test_format_memory_messages_unknown_type(mock_deps):
    """Test _format_memory_messages with unknown message type."""
    db, llm, memory = mock_deps
    trainer = AITrainerBrain(db, llm)

    class UnknownMessage:
        content = "Unknown content"
        type = "unknown"

    msg = UnknownMessage()
    result = trainer.format_history_as_messages([msg])


    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert "Unknown content" in result[0].content





def test_strip_internal_wrappers_preserves_generic_tags(mock_deps):
    """Only protocol tags are removed; regular data tags remain untouched."""
    db, llm, _ = mock_deps
    trainer = AITrainerBrain(db, llm)

    text = (
        '<msg data="03/04" hora="14:57">'
        '<treinador name="Atlas">'
        'Conteúdo <xml><item id="1">ok</item></xml>'
        "</treinador></msg>"
    )
    cleaned = trainer.strip_internal_wrappers(text)
    assert cleaned == 'Conteúdo <xml><item id="1">ok</item></xml>'
