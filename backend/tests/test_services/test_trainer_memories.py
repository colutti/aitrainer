import unittest
from unittest.mock import MagicMock, patch, ANY
# We need to ensure AITrainerBrain can be imported even if we strictly mock everything
from src.services.trainer import AITrainerBrain

class TestTrainerMemories(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        self.brain = AITrainerBrain(self.mock_db, self.mock_llm, self.mock_memory)

    def test_get_memories_paginated_empty(self):
        """Test retrieving paginated memories when empty."""
        mock_qdrant = MagicMock()
        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.count = 0
        mock_qdrant.count.return_value = mock_count_result

        memories, total = self.brain.get_memories_paginated(
            "user", 1, 10, mock_qdrant, "collection"
        )

        self.assertEqual(memories, [])
        self.assertEqual(total, 0)
        mock_qdrant.scroll.assert_not_called()

    def test_get_memories_paginated_success(self):
        """Test retrieving paginated memories successfully."""
        mock_qdrant = MagicMock()
        mock_count_result = MagicMock()
        mock_count_result.count = 25
        mock_qdrant.count.return_value = mock_count_result

        # Mock scroll behavior
        # Point 1 (New)
        p1 = MagicMock()
        p1.id = "1"
        p1.payload = {"id": "1", "memory": "Fact 1", "created_at": "2024-01-02T10:00:00"}
        
        # Point 2 (Old)
        p2 = MagicMock()
        p2.id = "2"
        p2.payload = {"id": "2", "memory": "Fact 2", "created_at": "2024-01-01T10:00:00"}
        
        # Return all points in one go
        mock_qdrant.scroll.return_value = ([p2, p1], None) # Unsorted initially

        # Request page 1 with size 1
        memories, total = self.brain.get_memories_paginated(
            "user", 1, 1, mock_qdrant, "collection"
        )

        self.assertEqual(total, 25)
        # Should be sorted Newest First (p1)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["id"], "1")
        self.assertEqual(memories[0]["memory"], "Fact 1")

    def test_get_memories_paginated_loop(self):
        """Test qdrant scrolling loop."""
        mock_qdrant = MagicMock()
        mock_count_result = MagicMock()
        mock_count_result.count = 200
        mock_qdrant.count.return_value = mock_count_result

        # Setup 2 batches
        p = MagicMock()
        p.payload = {"created_at": "2023"}
        
        mock_qdrant.scroll.side_effect = [
            ([p], "next_offset"), # Batch 1
            ([p], None)           # Batch 2 (Finish)
        ]

        memories, total = self.brain.get_memories_paginated(
            "user", 1, 10, mock_qdrant, "collection"
        )
        
        # Verify scroll called twice
        self.assertEqual(mock_qdrant.scroll.call_count, 2)
        self.assertEqual(len(memories), 2) # 2 points total returned/mocked

    def test_all_memories_fallback(self):
        """Test get_all_memories handles dictionary return from Mem0 (v1.0.1+ behavior)."""
        # Scenario: get_all returns {"results": [...]}
        self.mock_memory.get_all.return_value = {
            "results": [{"memory": "test", "created_at": "2024"}]
        }
        
        memories = self.brain.get_all_memories("user", limit=10)
        
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["memory"], "test")

    def test_all_memories_limit(self):
        """Test get_all_memories limits output."""
        self.mock_memory.get_all.return_value = [
            {"memory": "1", "created_at": "B"},
            {"memory": "2", "created_at": "A"} # Older
        ]
        
        # Sorts by created_at DESC -> B, A
        # Limit 1 -> B
        
        memories = self.brain.get_all_memories("user", limit=1)
        self.assertEqual(len(memories), 1)
        self.assertEqual(memories[0]["memory"], "1")
