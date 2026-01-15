
import pytest
from unittest.mock import MagicMock
from src.services.trainer import AITrainerBrain
from src.services.llm_client import LLMClient

def test_generate_insight_stream_integration():
    """
    Test that generate_insight_stream correctly calls the LLM client.
    This test uses the REAL AITrainerBrain but mocks the low-level LLMClient.
    """
    db = MagicMock()
    # Mock only the LLMClient, but keep the Brain real
    llm = MagicMock(spec=LLMClient)
    memory = MagicMock()

    # Mock DB cache lookup to return None (miss) to avoid comparison error
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    # Fix: MetabolismInsightCache accesses db.database["collection_name"]
    db.database.__getitem__.return_value = mock_collection
    
    # Mock the response from stream_simple
    def mock_stream(*args, **kwargs):
        yield "Part 1"
        yield "Part 2"
    llm.stream_simple.side_effect = mock_stream
    
    trainer = AITrainerBrain(db, llm, memory)
    
    # Mock trainer profile retrieval inside Brain
    mock_trainer_profile = MagicMock()
    mock_trainer_profile.get_trainer_profile_summary.return_value = "Expert"
    db.get_trainer_profile.return_value = mock_trainer_profile
    
    stats = {
        "startDate": "2024-01-01",
        "endDate": "2024-01-07",
        "logs_count": 7,
        "start_weight": 80,
        "end_weight": 79,
        "tdee": 2500,
        "avg_calories": 2000,
        "status": "deficit",
        "energy_balance": -500,
        "daily_target": 2000
    }
    
    # Execute the real implementation
    result = list(trainer.generate_insight_stream("user@test.com", stats))
    
    # Verify results
    assert result == ["Part 1", "Part 2"]
    
    # Verify that the brain called THE CORRECT method on LLMClient
    llm.stream_simple.assert_called_once()
    # This would fail if the brain still called 'stream_text'
