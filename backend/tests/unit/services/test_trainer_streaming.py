"""
Tests for AI Trainer streaming and error handling in src/services/trainer.py
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
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


@pytest.mark.asyncio
async def test_get_memories_paginated_error(mock_deps):

    """Test get_memories_paginated handling Qdrant error."""
    db, llm, memory = mock_deps
    db, llm, memory = mock_deps
    mock_qdrant = MagicMock()
    with patch("src.services.trainer.HistoryCompactor"):
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
    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm, qdrant_client)

    qdrant_client.retrieve.side_effect = Exception("Not found")

    result = trainer.get_memory_by_id("mem_id")
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
    result = trainer.format_history_as_messages([msg])


    assert len(result) == 1
    assert isinstance(result[0], HumanMessage)
    assert "Unknown content" in result[0].content


@pytest.mark.asyncio
async def test_send_message_ai_passes_image_payload_to_llm(mock_deps):
    """Ensure image payload is forwarded to LLM input data for multimodal flow."""
    db, llm, _ = mock_deps
    with patch("src.services.trainer.HistoryCompactor"):
        trainer = AITrainerBrain(db, llm)

    profile = MagicMock(subscription_plan="Pro", get_profile_summary=lambda: "User")
    trainer_profile = MagicMock(
        trainer_type="atlas", get_trainer_profile_summary=lambda: "Trainer"
    )
    trainer.get_or_create_user_profile = MagicMock(return_value=profile)
    trainer.get_or_create_trainer_profile = MagicMock(return_value=trainer_profile)
    trainer.check_message_limits = MagicMock(return_value=False)
    trainer.finalize_ai_response = AsyncMock()

    mock_memory_obj = MagicMock()
    mock_memory_obj.load_memory_variables.return_value = {"chat_history": []}
    db.get_window_memory.return_value = mock_memory_obj
    db.database = MagicMock()

    trainer.prompt_builder.build_input_data = MagicMock(
        return_value={"user_message": "Analyze this"}
    )
    prompt_template = MagicMock()
    trainer.prompt_builder.get_prompt_template = MagicMock(return_value=prompt_template)

    async def ok_stream(**_kwargs):
        yield "ok"
        yield {"type": "tools_summary", "tools_called": []}

    llm.stream_with_tools.side_effect = ok_stream

    image_payload = {"base64": "ZmFrZS1pbWFnZQ==", "mime_type": "image/jpeg"}
    chunks = []
    with patch("src.services.trainer.EventRepository") as mock_repo_cls:
        mock_repo_cls.return_value.get_active_events.return_value = []
        async for chunk in trainer.send_message_ai(
            user_email="pro@example.com",
            user_input="Analyze this",
            message_options={"image_payload": image_payload},
        ):
            chunks.append(chunk)

    assert "ok" in chunks
    called_input_data = llm.stream_with_tools.call_args.kwargs["input_data"]
    assert called_input_data["user_image"] == image_payload
