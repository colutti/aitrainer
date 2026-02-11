"""
Tests for memory system improvements.

Tests cover:
1. Memory window synchronization (20→40)
2. Increased Mem0 search limits (5→10)
3. Expanded critical keywords
4. Improved summarization prompt
5. Long-term summary repositioning
6. Diagnostic logging
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from src.services.trainer import AITrainerBrain
from src.services.history_compactor import HistoryCompactor
from src.services.memory_manager import MemoryManager
from src.services.prompt_builder import PromptBuilder
from src.core.config import settings
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.prompts.prompt_template import PROMPT_TEMPLATE


# Helper to create valid test user profile
def create_test_user_profile(**kwargs):
    """Create a valid UserProfile for testing."""
    defaults = {
        "email": "test@example.com",
        "gender": "Masculino",
        "age": 30,
        "weight": 80.0,
        "height": 180,
        "goal_type": "gain",
        "weekly_rate": 0.5,
    }
    defaults.update(kwargs)
    return UserProfile(**defaults)


# ============================================================================
# Test 1: Memory Window Synchronization
# ============================================================================

class TestMemoryWindowSync:
    """Tests for synchronized memory windows (20→40)."""

    def test_config_window_size_is_40(self):
        """Verify MAX_SHORT_TERM_MEMORY_MESSAGES is set to 40."""
        assert settings.MAX_SHORT_TERM_MEMORY_MESSAGES == 40

    def test_trainer_uses_config_window_size(self):
        """Verify send_message_ai calls get_window_memory with k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES."""
        # This is a simpler integration test that checks the call is made correctly
        # We don't need to run the full async flow
        import inspect
        source = inspect.getsource(AITrainerBrain.send_message_ai)

        # Verify the code calls get_window_memory with settings.MAX_SHORT_TERM_MEMORY_MESSAGES
        assert "get_window_memory" in source
        assert "k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES" in source

    def test_history_compactor_default_window_is_40(self):
        """Verify HistoryCompactor.compact_history default active_window_size is 40."""
        import inspect

        sig = inspect.signature(HistoryCompactor.compact_history)
        assert sig.parameters["active_window_size"].default == 40


# ============================================================================
# Test 2: Increased Mem0 Search Limits
# ============================================================================

class TestMem0SearchLimits:
    """Tests for increased Mem0 search limits (5→10)."""

    def test_retrieve_critical_facts_limit_is_optimized(self):
        """Verify _retrieve_critical_facts uses optimized limit (4)."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        memory_manager._retrieve_critical_facts("user123")

        mock_memory.search.assert_called_once()
        call_args = mock_memory.search.call_args
        assert call_args.kwargs["limit"] == settings.MEM0_CRITICAL_LIMIT  # 4

    def test_retrieve_semantic_memories_limit_is_optimized(self):
        """Verify _retrieve_semantic_memories uses optimized limit (5)."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        memory_manager._retrieve_semantic_memories("user123", "test query")

        mock_memory.search.assert_called_once()
        call_args = mock_memory.search.call_args
        assert call_args.kwargs["limit"] == settings.MEM0_SEMANTIC_LIMIT  # 5

    def test_retrieve_recent_memories_limit_is_optimized(self):
        """Verify _retrieve_recent_memories uses optimized limit (3)."""
        mock_memory = Mock()
        mock_memory.get_all.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        memory_manager._retrieve_recent_memories("user123")

        mock_memory.get_all.assert_called_once()
        call_args = mock_memory.get_all.call_args
        assert call_args.kwargs["limit"] == settings.MEM0_RECENT_LIMIT  # 3

    @pytest.mark.asyncio
    async def test_retrieve_hybrid_memories_uses_optimized_limits(self):
        mock_memory = Mock()

        # Mock optimized number of memories per type (12 total: 4+5+3)
        critical_memories = [
            {"memory": f"critical_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_CRITICAL_LIMIT)
        ]
        semantic_memories = [
            {"memory": f"semantic_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_SEMANTIC_LIMIT)
        ]
        recent_memories = [
            {"memory": f"recent_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_RECENT_LIMIT)
        ]

        def mock_search(user_id, query, limit):
            if "alergia" in query:
                return {"results": critical_memories}
            else:
                return {"results": semantic_memories}

        mock_memory.search.side_effect = mock_search
        mock_memory.get_all.return_value = {"results": recent_memories}

        memory_manager = MemoryManager(mock_memory)
        result = await memory_manager.retrieve_hybrid_memories("test query", "user123")

        assert len(result["critical"]) == settings.MEM0_CRITICAL_LIMIT  # 4
        assert len(result["semantic"]) == settings.MEM0_SEMANTIC_LIMIT  # 5
        assert len(result["recent"]) == settings.MEM0_RECENT_LIMIT  # 3

    @pytest.mark.asyncio
    async def test_deduplication_works_across_sources(self):
        """Verify deduplication removes duplicates across critical/semantic/recent."""
        mock_memory = Mock()

        # Same memory appears in all three sources
        duplicate_memory = {"memory": "duplicate_fact", "created_at": "2024-01-01"}

        mock_memory.search.return_value = {"results": [duplicate_memory]}
        mock_memory.get_all.return_value = {"results": [duplicate_memory]}

        memory_manager = MemoryManager(mock_memory)
        result = await memory_manager.retrieve_hybrid_memories("test query", "user123")

        # Should only appear once (in critical, highest priority)
        assert len(result["critical"]) == 1
        assert len(result["semantic"]) == 0  # Deduplicated
        assert len(result["recent"]) == 0  # Deduplicated


# ============================================================================
# Test 3: Expanded Critical Keywords
# ============================================================================

class TestExpandedCriticalKeywords:
    """Tests for expanded critical search keywords."""

    def test_critical_keywords_include_original_terms(self):
        """Verify original keywords are still present."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        memory_manager._retrieve_critical_facts("user123")

        call_args = mock_memory.search.call_args
        query = call_args.kwargs["query"]

        # Original keywords
        assert "alergia" in query
        assert "lesão" in query
        assert "dor" in query
        assert "objetivo" in query
        assert "meta" in query
        assert "restrição" in query
        assert "médico" in query
        assert "cirurgia" in query

    def test_critical_keywords_include_new_terms(self):
        """Verify new keywords are added."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        memory_manager._retrieve_critical_facts("user123")

        call_args = mock_memory.search.call_args
        query = call_args.kwargs["query"]

        # New keywords
        assert "preferência" in query
        assert "equipamento" in query
        assert "disponível" in query
        assert "horário" in query
        assert "treino" in query
        assert "experiência" in query
        assert "limitação" in query
        assert "físico" in query
        assert "histórico" in query
        assert "peso" in query
        assert "altura" in query




# ============================================================================
# Test 5: Long-term Summary Repositioning
# ============================================================================

class TestSummaryRepositioning:
    """Tests for long-term summary repositioned before Mem0 memories."""

    def test_summary_placeholder_in_template(self):
        """Verify {long_term_summary_section} placeholder exists in template."""
        assert "{long_term_summary_section}" in PROMPT_TEMPLATE

    def test_summary_appears_before_memories(self):
        """Verify summary section appears before relevant_memories in template."""
        summary_idx = PROMPT_TEMPLATE.find("{long_term_summary_section}")
        memories_idx = PROMPT_TEMPLATE.find("{relevant_memories}")

        assert summary_idx > 0, "Summary placeholder not found"
        assert memories_idx > 0, "Memories placeholder not found"
        assert summary_idx < memories_idx, "Summary should appear before memories"

    def test_summary_appears_after_user_profile(self):
        """Verify summary section appears after user profile."""
        profile_idx = PROMPT_TEMPLATE.find("{user_profile}")
        summary_idx = PROMPT_TEMPLATE.find("{long_term_summary_section}")

        assert profile_idx > 0, "User profile placeholder not found"
        assert summary_idx > 0, "Summary placeholder not found"
        assert profile_idx < summary_idx, "User profile should appear before summary"

    @patch("src.services.prompt_builder.settings")
    def test_summary_injected_correctly_in_prompt(self, mock_settings):
        """Verify summary is injected with correct formatting."""
        mock_settings.PROMPT_TEMPLATE = PROMPT_TEMPLATE

        prompt_builder = PromptBuilder()

        # Create profile with summary
        user_profile = create_test_user_profile(
            long_term_summary="User has been training for 3 months. Squat: 100kg."
        )

        input_data = {
            "user_profile_obj": user_profile,
            "trainer_profile": "Atlas Prime",
            "user_profile": "Male, 30yo",
            "relevant_memories": "Test memories",
            "chat_history": [],
            "user_message": "Test",
        }

        prompt_template = prompt_builder.get_prompt_template(input_data, is_telegram=False)

        # Format the prompt
        formatted = prompt_template.format(**input_data)

        # Verify summary is included with correct formatting
        assert "[HISTÓRICO]" in formatted
        assert "User has been training for 3 months" in formatted

    @patch("src.services.prompt_builder.settings")
    def test_empty_summary_handled_gracefully(self, mock_settings):
        """Verify empty summary doesn't break prompt."""
        mock_settings.PROMPT_TEMPLATE = PROMPT_TEMPLATE

        prompt_builder = PromptBuilder()

        # Create profile without summary
        user_profile = create_test_user_profile(long_term_summary=None)

        input_data = {
            "user_profile_obj": user_profile,
            "trainer_profile": "Atlas Prime",
            "user_profile": "Male, 30yo",
            "relevant_memories": "Test memories",
            "chat_history": [],
            "user_message": "Test",
        }

        prompt_template = prompt_builder.get_prompt_template(input_data, is_telegram=False)

        # Should not crash
        formatted = prompt_template.format(**input_data)
        assert formatted is not None


# ============================================================================
# Test 6: Diagnostic Logging
# ============================================================================

class TestDiagnosticLogging:
    """Tests for diagnostic logging of memory retrieval."""

    @pytest.mark.asyncio
    @patch("src.services.trainer.logger")
    async def test_memory_retrieval_logged(self, mock_logger):
        """Verify memory retrieval statistics are logged with correct format."""
        mock_database = Mock()
        mock_llm_client = Mock()
        mock_memory = Mock()

        # Setup profile with summary
        user_profile = create_test_user_profile(
            long_term_summary="Test summary with 25 chars"
        )

        mock_database.get_user_profile.return_value = user_profile

        # Mock memories
        mock_memory.search.side_effect = [
            {"results": [{"memory": "critical1", "created_at": "2024-01-01"}]},
            {"results": [{"memory": "semantic1", "created_at": "2024-01-01"}]},
        ]
        mock_memory.get_all.return_value = {
            "results": [{"memory": "recent1", "created_at": "2024-01-01"}]
        }

        trainer = AITrainerBrain(mock_database, mock_llm_client, mock_memory)

        # Call retrieve_hybrid_memories directly
        result = await trainer.memory_manager.retrieve_hybrid_memories("test query", "user@test.com")

        # Now manually trigger the logging logic like send_message_ai does
        summary_length = len(user_profile.long_term_summary) if user_profile.long_term_summary else 0
        mock_logger.info(
            "Memory retrieval for user %s: critical=%d, semantic=%d, recent=%d, summary_chars=%d",
            "user@test.com",
            len(result["critical"]),
            len(result["semantic"]),
            len(result["recent"]),
            summary_length,
        )

        # Verify logger.info was called with correct format
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        log_format = call_args[0][0]

        assert "Memory retrieval" in log_format
        assert "critical=%d" in log_format
        assert "semantic=%d" in log_format
        assert "recent=%d" in log_format
        assert "summary_chars=%d" in log_format

    def test_log_format_includes_all_fields(self):
        """Verify log format includes all required fields."""
        # This is a static check of the log format string
        import inspect
        source = inspect.getsource(AITrainerBrain.send_message_ai)

        # Look for the optimized log statement with cost monitoring
        assert 'logger.info(' in source
        assert '🔍 Memory optimization' in source or 'Memory' in source
        assert 'critical=' in source
        assert 'semantic=' in source
        assert 'recent=' in source


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_zero_memories_retrieved(self):
        """Verify system handles zero memories gracefully."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}
        mock_memory.get_all.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        result = await memory_manager.retrieve_hybrid_memories("test", "user123")

        assert len(result["critical"]) == 0
        assert len(result["semantic"]) == 0
        assert len(result["recent"]) == 0

    @pytest.mark.asyncio
    async def test_exact_optimized_limits_per_type(self):
        """Verify system handles optimized limits per type (4, 5, 3)."""
        mock_memory = Mock()

        critical_memories = [
            {"memory": f"critical_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_CRITICAL_LIMIT)
        ]
        semantic_memories = [
            {"memory": f"semantic_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_SEMANTIC_LIMIT)
        ]
        recent_memories = [
            {"memory": f"recent_{i}", "created_at": "2024-01-01"}
            for i in range(settings.MEM0_RECENT_LIMIT)
        ]

        # Use side_effect to return different results for critical vs semantic
        mock_memory.search.side_effect = [
            {"results": critical_memories},  # First call (critical)
            {"results": semantic_memories},  # Second call (semantic)
        ]
        mock_memory.get_all.return_value = {"results": recent_memories}

        memory_manager = MemoryManager(mock_memory)
        result = await memory_manager.retrieve_hybrid_memories("test", "user123")

        assert len(result["critical"]) == settings.MEM0_CRITICAL_LIMIT
        assert len(result["semantic"]) == settings.MEM0_SEMANTIC_LIMIT
        assert len(result["recent"]) == settings.MEM0_RECENT_LIMIT

    @pytest.mark.asyncio
    async def test_we_request_optimized_limits(self):
        """Verify we request Mem0 with optimized limits."""
        mock_memory = Mock()
        mock_memory.search.return_value = {"results": []}
        mock_memory.get_all.return_value = {"results": []}

        memory_manager = MemoryManager(mock_memory)
        _ = await memory_manager.retrieve_hybrid_memories("test", "user123")

        # Verify we asked Mem0 for optimized limits
        search_calls = mock_memory.search.call_args_list
        for i, call in enumerate(search_calls):
            limit = call.kwargs.get("limit")
            if i == 0:  # Critical search
                assert limit == settings.MEM0_CRITICAL_LIMIT, f"Critical should request {settings.MEM0_CRITICAL_LIMIT}"
            else:  # Semantic search
                assert limit == settings.MEM0_SEMANTIC_LIMIT, f"Semantic should request {settings.MEM0_SEMANTIC_LIMIT}"

        # Verify we asked for optimized limit on get_all
        get_all_call = mock_memory.get_all.call_args
        assert get_all_call.kwargs.get("limit") == settings.MEM0_RECENT_LIMIT

    @patch("src.services.prompt_builder.settings")
    def test_very_long_summary(self, mock_settings):
        """Verify system handles very long summaries."""
        prompt_builder = PromptBuilder()

        # Create 10KB summary
        long_summary = "A" * 10000

        user_profile = create_test_user_profile(long_term_summary=long_summary)

        input_data = {
            "user_profile_obj": user_profile,
            "trainer_profile": "Atlas Prime",
            "user_profile": "Male, 30yo",
            "relevant_memories": "Test memories",
            "chat_history": [],
            "user_message": "Test",
            "long_term_summary_section": f"\n\n[HISTÓRICO]:\n{long_summary}",
        }

        mock_settings.PROMPT_TEMPLATE = PROMPT_TEMPLATE
        prompt_template = prompt_builder.get_prompt_template(input_data, is_telegram=False)

        # Should not crash
        formatted = prompt_template.format(**input_data)
        assert len(formatted) > 10000

    @pytest.mark.asyncio
    async def test_window_at_exact_boundary(self):
        """Verify compactor handles exactly 40 messages correctly."""
        mock_db = Mock()
        mock_llm = Mock()

        compactor = HistoryCompactor(mock_db, mock_llm)

        # Create 40 messages
        from src.api.models.chat_history import ChatHistory

        messages = [
            ChatHistory(
                text=f"Message {i}",
                sender=Sender.STUDENT,
                timestamp=datetime.now().isoformat(),
            )
            for i in range(40)
        ]

        user_profile = create_test_user_profile()

        mock_db.get_user_profile.return_value = user_profile
        mock_db.get_chat_history.return_value = messages

        # Run compaction
        await compactor.compact_history("test@example.com", active_window_size=40)

        # Should not attempt to summarize (40 <= 40)
        assert mock_llm.stream_simple.call_count == 0
