import os
import sys
import time
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from src.services.trainer import AITrainerBrain
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from mem0 import Memory

def benchmark_send_message():
    # Setup mocks
    mock_db = MagicMock(spec=MongoDatabase)
    mock_db.workouts_repo = MagicMock()
    mock_llm = MagicMock(spec=LLMClient)
    mock_memory = MagicMock(spec=Memory)

    # Mock DB responses with simulated latency (100ms total if sequential, 50ms if parallel)
    def mocked_get_profile(*args, **kwargs):
        time.sleep(0.05) # Simulate DB latency
        m = MagicMock()
        m.trainer_type = "atlas"
        m.get_trainer_profile_summary.return_value = "Mock Trainer Summary"
        m.get_profile_summary.return_value = "Mock User Summary"
        m.long_term_summary = None
        return m

    mock_db.get_user_profile.side_effect = mocked_get_profile
    mock_db.get_trainer_profile.side_effect = mocked_get_profile
    
    # Mock Mem0 responses with simulated latency (450ms total if sequential, 150ms if parallel)
    def mocked_search(*args, **kwargs):
        time.sleep(0.15) # Simulate search latency
        return {"results": []}

    mock_memory.search.side_effect = mocked_search
    mock_memory.get_all.return_value = []

    # Mock LLM stream
    def mock_stream(*args, **kwargs):
        for chunk in ["AI ", "response ", "stream"]:
            # yield chunk
            pass
        yield "Done"

    mock_llm.stream_with_tools.side_effect = mock_stream

    # Initialize brain with mocks
    brain = AITrainerBrain(database=mock_db, llm_client=mock_llm, memory=mock_memory)

    print("Benchmarking send_message_ai (Parallel version)...")
    start_time = time.time()
    
    # We call it with a fake background_tasks to trigger the path
    from fastapi import BackgroundTasks
    bg = BackgroundTasks()

    generator = brain.send_message_ai(
        user_email="test@example.com",
        user_input="Hello",
        background_tasks=bg
    )
    
    # Measure time to first chunk
    next(generator)
    ttft = time.time() - start_time
    print(f"Time to First Chunk (TTFT): {ttft:.4f}s")
    
    # Exhaust generator
    for _ in generator:
        pass
    
    total_time = time.time() - start_time
    print(f"Total loop time: {total_time:.4f}s")
    
    # Confidence check: 
    # Sequential would be: 2*50ms (profiles) + 3*150ms (memories) = 550ms + some overhead.
    # Parallel should be: 1*50ms (profiles) + 1*150ms (memories) = 200ms + some overhead.
    
    if ttft < 0.35:
        print("✅ SUCCESS: Parallelization is working. Latency is within expected range (< 350ms).")
    else:
        print("❌ FAILURE: Latency is higher than expected. Check implementation.")

if __name__ == "__main__":
    benchmark_send_message()
