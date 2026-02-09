"""
Tests for memory optimization features.

Validates:
- Reduced memory limits from config
- Semantic deduplication
- Context size limiting
- Compact formatting
"""

import pytest
from unittest.mock import Mock
from datetime import datetime, timedelta
from src.services.memory_manager import MemoryManager
from src.core.config import settings
from src.core.logs import logger


class TestMemoryLimitsOptimization:
    """Test that memory limits have been reduced for cost optimization."""

    def test_critical_limit_reduced(self):
        """Verify critical memory limit is reduced (4 instead of 10)."""
        assert settings.MEM0_CRITICAL_LIMIT == 4, \
            f"Critical limit should be 4, got {settings.MEM0_CRITICAL_LIMIT}"

    def test_semantic_limit_reduced(self):
        """Verify semantic memory limit is reduced (5 instead of 10)."""
        assert settings.MEM0_SEMANTIC_LIMIT == 5, \
            f"Semantic limit should be 5, got {settings.MEM0_SEMANTIC_LIMIT}"

    def test_recent_limit_reduced(self):
        """Verify recent memory limit is reduced (3 instead of 10)."""
        assert settings.MEM0_RECENT_LIMIT == 3, \
            f"Recent limit should be 3, got {settings.MEM0_RECENT_LIMIT}"

    def test_max_context_size_limit(self):
        """Verify max context size is set (1024 bytes)."""
        assert settings.MEM0_MAX_CONTEXT_SIZE == 1024, \
            f"Max context should be 1024 bytes, got {settings.MEM0_MAX_CONTEXT_SIZE}"


class TestSemanticDeduplication:
    """Test semantic deduplication functionality."""

    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager with mocked Mem0."""
        mock_memory = Mock()
        return MemoryManager(mock_memory)

    def test_cosine_similarity_identical_vectors(self, memory_manager):
        """Test cosine similarity with identical vectors (should be 1.0)."""
        vec = [1.0, 0.0, 0.0]
        similarity = memory_manager._cosine_similarity(vec, vec)
        assert abs(similarity - 1.0) < 0.001, f"Identical vectors should have similarity 1.0, got {similarity}"

    def test_cosine_similarity_orthogonal_vectors(self, memory_manager):
        """Test cosine similarity with orthogonal vectors (should be 0.0)."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = memory_manager._cosine_similarity(vec1, vec2)
        assert abs(similarity) < 0.001, f"Orthogonal vectors should have similarity 0.0, got {similarity}"

    def test_cosine_similarity_similar_vectors(self, memory_manager):
        """Test cosine similarity with similar vectors."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.95, 0.1, 0.0]  # Similar but not identical
        similarity = memory_manager._cosine_similarity(vec1, vec2)
        assert 0.9 < similarity < 1.0, f"Similar vectors should have high similarity, got {similarity}"

    def test_deduplicate_exact_duplicates(self, memory_manager):
        """Test deduplication of exact text duplicates."""
        memories = [
            {"text": "Push 2x/semana", "created_at": "2026-02-03T10:00:00", "embedding": None},
            {"text": "Push 2x/semana", "created_at": "2026-02-02T10:00:00", "embedding": None},
        ]
        result = memory_manager._deduplicate_semantically(memories)
        assert len(result) == 1, f"Should have 1 memory after dedup, got {len(result)}"
        assert result[0]["created_at"] == "2026-02-03T10:00:00", "Should keep most recent"

    def test_deduplicate_semantic_duplicates(self, memory_manager):
        """Test deduplication of semantically similar memories."""
        memories = [
            {
                "text": "Push 2x/semana",
                "created_at": "2026-02-03T10:00:00",
                "embedding": [1.0, 0.0, 0.0],
            },
            {
                "text": "Treino Push duas vezes por semana",
                "created_at": "2026-02-02T10:00:00",
                "embedding": [0.98, 0.05, 0.0],  # Very similar embedding
            },
        ]
        result = memory_manager._deduplicate_semantically(memories, threshold=0.9)
        assert len(result) == 1, f"Should detect semantic duplicate, got {len(result)} memories"

    def test_deduplicate_keeps_diverse_memories(self, memory_manager):
        """Test that diverse memories are kept."""
        memories = [
            {
                "text": "Push 2x/semana",
                "created_at": "2026-02-03T10:00:00",
                "embedding": [1.0, 0.0, 0.0],
            },
            {
                "text": "Leg Press 4 séries",
                "created_at": "2026-02-02T10:00:00",
                "embedding": [0.0, 1.0, 0.0],  # Very different
            },
        ]
        result = memory_manager._deduplicate_semantically(memories, threshold=0.85)
        assert len(result) == 2, f"Should keep all diverse memories, got {len(result)}"


class TestCompactFormatting:
    """Test compact formatting of memories."""

    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager with mocked Mem0."""
        mock_memory = Mock()
        return MemoryManager(mock_memory)

    def test_format_date_hides_recent(self, memory_manager):
        """Test that recent dates (< 7 days) are hidden."""
        now = datetime.now()
        recent_date = (now - timedelta(days=2)).isoformat()
        result = memory_manager._format_date(recent_date)
        assert result == "", f"Recent date should be hidden, got '{result}'"

    def test_format_date_shows_old(self, memory_manager):
        """Test that old dates (>= 7 days) are shown."""
        now = datetime.now()
        old_date = (now - timedelta(days=10)).isoformat()
        result = memory_manager._format_date(old_date)
        assert result != "", f"Old date should be shown, got '{result}'"
        assert "/" in result, f"Date should have dd/mm format, got '{result}'"

    def test_format_memories_respects_size_limit(self, memory_manager):
        """Test that formatted memories respect max size limit."""
        hybrid_memories = {
            "critical": [
                {"text": "A" * 500, "created_at": "2026-02-03T10:00:00"},
                {"text": "B" * 500, "created_at": "2026-02-02T10:00:00"},
            ],
            "semantic": [],
            "recent": [],
        }
        result = memory_manager.format_memories(hybrid_memories)
        assert len(result) <= settings.MEM0_MAX_CONTEXT_SIZE + 100, \
            f"Formatted memories should respect size limit, got {len(result)} bytes"

    def test_format_memories_compact_style(self, memory_manager):
        """Test that formatted memories use compact style."""
        now = datetime.now()
        old_date = (now - timedelta(days=10)).isoformat()

        hybrid_memories = {
            "critical": [
                {"text": "Test memory", "created_at": old_date},
            ],
            "semantic": [],
            "recent": [],
        }
        result = memory_manager.format_memories(hybrid_memories)
        # Should use "- Text [dd/mm]" format, not "(dd/mm) Text"
        assert "- Test memory [" in result, f"Should use compact format, got: {result}"


class TestMemoryIntegration:
    """Integration tests for full memory optimization."""

    @pytest.fixture
    def memory_manager(self):
        """Create a memory manager with mocked Mem0."""
        mock_memory = Mock()
        return MemoryManager(mock_memory)

    def test_retrieve_hybrid_with_reduced_limits(self, memory_manager):
        """Test that hybrid retrieval uses optimized limits."""
        # Mock the Mem0 search results
        mock_memory = memory_manager._memory
        mock_memory.search.return_value = {
            "results": [
                {"memory": f"Memory {i}", "created_at": "2026-02-03T10:00:00"}
                for i in range(5)
            ]
        }
        mock_memory.get_all.return_value = {
            "results": [
                {"memory": f"Recent {i}", "created_at": "2026-02-03T10:00:00"}
                for i in range(5)
            ]
        }

        _ = memory_manager.retrieve_hybrid_memories("test query", "user123")

        # Verify that search was called with optimized limits
        search_calls = mock_memory.search.call_args_list
        for call in search_calls:
            limit = call.kwargs.get("limit", call[1] if len(call) > 1 else None)
            assert limit in [4, 5], f"Expected optimized limit (4 or 5), got {limit}"

    def test_end_to_end_cost_reduction(self, memory_manager):
        """Test that overall formatting results in smaller context."""
        # Create sample memories (30 memories -> should reduce to ~12)
        memories = [
            {"text": f"Memory {i}", "created_at": "2026-02-03T10:00:00", "embedding": None}
            for i in range(30)
        ]

        hybrid_memories = {
            "critical": memories[:10],
            "semantic": memories[10:20],
            "recent": memories[20:30],
        }

        formatted = memory_manager.format_memories(hybrid_memories)

        # Old system would produce ~1500+ chars (30 memories * ~50 chars each + headers + dates)
        # New system should produce ~800 chars or less (compact formatting + reduced limits)
        assert len(formatted) < 1500, \
            f"Formatted memories too large: {len(formatted)} chars (should be < 1500 with optimization)"

        # Estimate tokens (1 token ≈ 4 chars)
        estimated_tokens = len(formatted) // 4
        logger.info(f"Memory context: {len(formatted)} chars ≈ {estimated_tokens} tokens")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
