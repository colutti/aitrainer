"""
Tests for AI Trainer streaming and error handling in src/services/trainer.py
"""
import pytest
from unittest.mock import MagicMock, patch, ANY
from src.services.trainer import AITrainerBrain
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender

@pytest.fixture
def mock_deps():
    db = MagicMock()
    llm = MagicMock()
    memory = MagicMock()
    return db, llm, memory

def test_send_message_ai_streaming_error(mock_deps):
    """Test streaming response when an error occurs mid-stream."""
    db, llm, memory = mock_deps
    
    with patch('src.services.trainer.HistoryCompactor'):
        trainer = AITrainerBrain(db, llm, memory)
    
    # Mock user and trainer profiles
    db.get_user_profile.return_value = MagicMock(
        get_profile_summary=lambda: "User Summary"
    )
    db.get_trainer_profile.return_value = MagicMock(
        trainer_type="atlas",
        get_trainer_profile_summary=lambda: "Trainer Summary"
    )
    
    # Mock conversation memory and variables
    mock_memory_obj = MagicMock()
    mock_memory_obj.load_memory_variables.return_value = {"chat_history": []}
    mock_memory_obj = MagicMock()
    mock_memory_obj.load_memory_variables.return_value = {"chat_history": []}
    db.get_window_memory.return_value = mock_memory_obj
    
    # Mock stream to fail after first chunk
    def error_stream(**kwargs):
        yield "First chunk"
        raise Exception("Stream failed")
        
    llm.stream_with_tools.side_effect = error_stream
    
    # Execute generator
    gen = trainer.send_message_ai("user@test.com", "Hello")
    
    with pytest.raises(Exception, match="Stream failed"):
        first = next(gen)
        assert first == "First chunk"
        next(gen) # Should raise

def test_add_to_mem0_background_success():
    """Test background task adding to Mem0 successfully."""
    from src.services.trainer import _add_to_mem0_background
    
    memory = MagicMock()
    _add_to_mem0_background(memory, "user@test.com", "Hello", "Response")
    
    memory.add.assert_called_once()
    args = memory.add.call_args[0][0]
    assert len(args) == 2
    assert args[0]["role"] == "user"
    assert args[1]["role"] == "assistant"

def test_add_to_mem0_background_failure():
    """Test background task handling Mem0 failure silently."""
    from src.services.trainer import _add_to_mem0_background
    
    memory = MagicMock()
    memory.add.side_effect = Exception("Mem0 error")
    
    # Should not raise exception
    _add_to_mem0_background(memory, "user@test.com", "Hello", "Response")
    memory.add.assert_called_once()

def test_get_memories_paginated_error(mock_deps):
    """Test get_memories_paginated handling Qdrant error."""
    db, llm, memory = mock_deps
    db, llm, memory = mock_deps
    with patch('src.services.trainer.HistoryCompactor'):
        trainer = AITrainerBrain(db, llm, memory)
    
    mock_qdrant = MagicMock()
    mock_qdrant.count.side_effect = Exception("Qdrant unavailable")
    
    with pytest.raises(Exception, match="Qdrant unavailable"):
        trainer.get_memories_paginated(
            "user@test.com", 1, 10, mock_qdrant, "test_collection"
        )

def test_get_memory_by_id_error(mock_deps):
    """Test get_memory_by_id handling error gracefully."""
    db, llm, memory = mock_deps
    db, llm, memory = mock_deps
    with patch('src.services.trainer.HistoryCompactor'):
        trainer = AITrainerBrain(db, llm, memory)
    
    memory.get.side_effect = Exception("Not found")
    
    result = trainer.get_memory_by_id("mem_id")
    assert result is None

def test_normalize_mem0_results_list_response(mock_deps):
    """Test _normalize_mem0_results handling list response from Mem0."""
    db, llm, memory = mock_deps
    with patch('src.services.trainer.HistoryCompactor'):
        trainer = AITrainerBrain(db, llm, memory)
    
    # Mock result list
    results = [
        {"memory": "Fact 1", "created_at": "2024-01-01"}
    ]
    
    facts = trainer._normalize_mem0_results(results, "test_source")
    assert len(facts) == 1
    assert facts[0]["text"] == "Fact 1"
    assert facts[0]["source"] == "test_source"

def test_format_memory_messages_unknown_type(mock_deps):
    """Test _format_memory_messages with unknown message type."""
    db, llm, memory = mock_deps
    with patch('src.services.trainer.HistoryCompactor'):
        trainer = AITrainerBrain(db, llm, memory)
    
    class UnknownMessage:
        content = "Unknown content"
        
    msg = UnknownMessage()
    result = trainer._format_memory_messages([msg], "atlas")
    
    assert "> Unknown content" in result
