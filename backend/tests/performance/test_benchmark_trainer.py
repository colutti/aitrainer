
import pytest
from unittest.mock import MagicMock
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile

@pytest.fixture
def trainer_brain():
    mock_db = MagicMock()
    mock_llm = MagicMock()
    mock_memory = MagicMock()
    
    # 1. Profile Retrieval Mock
    mock_user_profile = MagicMock(spec=UserProfile)
    mock_user_profile.long_term_summary = "User summary"
    mock_user_profile.get_profile_summary.return_value = "User Profile Summary"
    mock_db.get_user_profile.return_value = mock_user_profile
    
    mock_trainer_profile = MagicMock(spec=TrainerProfile)
    mock_trainer_profile.trainer_type = "atlas"
    mock_trainer_profile.get_trainer_profile_summary.return_value = "Trainer Profile Summary"
    mock_db.get_trainer_profile.return_value = mock_trainer_profile
    
    # 2. Memory Retrieval Mock
    # Hybrid search returns dict
    mock_memory.search.return_value = [{"text": "Found memory", "created_at": "2024-01-01"}]
    mock_memory.get_all.return_value = [{"text": "Recent memory", "created_at": "2024-01-01"}]
    
    # 3. Short Term Window Memory
    mock_window_memory = MagicMock()
    mock_window_memory.load_memory_variables.return_value = {
        "chat_history": [
            MagicMock(content="Hello", type="human", additional_kwargs={}),
            MagicMock(content="Hi there", type="ai", additional_kwargs={"trainer_type": "atlas"})
        ]
    }
    mock_db.get_window_memory.return_value = mock_window_memory
    
    # 4. LLM Client Mock
    # stream_with_tools returns an async generator
    async def mock_stream(*args, **kwargs):
        yield "This is a mocked AI response based on the input."
    
    mock_llm.stream_with_tools.side_effect = mock_stream
    
    brain = AITrainerBrain(mock_db, mock_llm, mock_memory)
    return brain

def test_benchmark_send_message_sync(benchmark, trainer_brain):
    """
    Benchmarks the pure Python logic overhead of the send_message_sync pipeline:
    - Parallel profile fetching
    - Hybrid memory search (ThreadPool)
    - Context construction
    - Prompt formatting
    - Tool initialization
    """
    def run_logic():
        # user_email acts as session_id
        trainer_brain.send_message_sync(
            user_email="bench@test.com",
            user_input="How is my diet?",
            is_telegram=False
        )
        
    benchmark(run_logic)
