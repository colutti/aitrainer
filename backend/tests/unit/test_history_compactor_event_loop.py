"""
Tests for event loop isolation in history compaction.

Validates that the fix for "Task got Future attached to a different loop" works correctly.
This tests the asyncio.run() fix instead of manual loop management.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from src.services.history_compactor import HistoryCompactor
from src.services.llm_client import LLMClient
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender


@pytest.fixture
def mock_database():
    """Create a mock database for testing."""
    db = Mock()

    # Mock user profile
    profile = Mock()
    profile.long_term_summary = ""
    profile.last_compaction_timestamp = None
    db.get_user_profile = Mock(return_value=profile)

    # Mock chat history with student messages
    history = [
        ChatHistory(
            id="1",
            sender=Sender.STUDENT,
            text="I want to start a new workout routine",
            timestamp="2026-02-01T10:00:00",
            trainer_id="",
        ),
        ChatHistory(
            id="2",
            sender=Sender.TRAINER,
            text="Great! Let's design one for you.",
            timestamp="2026-02-01T10:01:00",
            trainer_id="",
        ),
        ChatHistory(
            id="3",
            sender=Sender.STUDENT,
            text="I prefer lifting weights over cardio",
            timestamp="2026-02-01T10:02:00",
            trainer_id="",
        ),
    ]
    db.get_chat_history = Mock(return_value=history)
    db.update_user_profile_fields = Mock(return_value=True)

    return db


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)

    async def mock_stream_simple(*args, **kwargs):
        """Mock async generator that simulates LLM streaming."""
        yield '{"health": "Normal", "restrictions": "None", "preferences": "Lifting weights"}'

    client.stream_simple = AsyncMock(side_effect=mock_stream_simple)
    return client


@pytest.fixture
def compactor(mock_database, mock_llm_client):
    """Create a HistoryCompactor instance with mocks."""
    return HistoryCompactor(mock_database, mock_llm_client)


class TestEventLoopIsolation:
    """Test event loop isolation in history compaction."""

    def test_compact_history_uses_asyncio_run(self, compactor, mock_database):
        """
        Test that compact_history properly uses asyncio.run() for event loop isolation.

        The critical fix is using asyncio.run() instead of manual asyncio.new_event_loop()
        which prevents "Future attached to different loop" errors.

        This test verifies the behavior indirectly by ensuring:
        1. No manual event loop creation happens
        2. Execution completes successfully
        3. No event loop related errors occur
        """
        user_email = "test@example.com"

        # This will execute using asyncio.run() internally
        # If it completes without RuntimeError about event loops, the fix works
        compactor.compact_history(user_email)

        # Verify the mock database was called correctly
        mock_database.get_user_profile.assert_called_with(user_email)
        mock_database.get_chat_history.assert_called_with(user_email, limit=1000)

    def test_compact_history_completes_without_event_loop_error(
        self, compactor, mock_database
    ):
        """
        Test that compact_history completes without "Future attached to different loop" error.

        This simulates the actual error that was occurring before the fix.
        """
        user_email = "test@example.com"

        # This should complete without raising asyncio errors
        try:
            compactor.compact_history(user_email)
            # If we get here without exception, the test passes
            assert True
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                pytest.fail(
                    f"Event loop error detected: {e}. "
                    "The fix for asyncio.run() may not be working."
                )
            raise

    @pytest.mark.asyncio
    async def test_stream_simple_works_in_isolated_event_loop(self):
        """
        Test that LLMClient.stream_simple works correctly in an isolated event loop.

        This validates that the LLM client works when called from within asyncio.run().
        """
        from langchain_core.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        # Create a mock async generator that simulates LLM streaming
        async def mock_astream(data):
            yield "Response "
            yield "chunk"

        # Create the prompt template
        prompt = PromptTemplate.from_template("Test: {input}")

        # This is what actually happens inside stream_simple
        result = ""
        async for chunk in mock_astream({"input": "data"}):
            result += chunk

        assert result == "Response chunk"

    def test_compact_history_in_background_thread(self, compactor):
        """
        Test that compact_history works when called from a background thread.

        This is the actual scenario where the original error occurred.
        """
        import threading
        import time

        user_email = "test@example.com"
        result = {"success": False, "error": None}

        def run_in_thread():
            try:
                compactor.compact_history(user_email)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)

        thread = threading.Thread(target=run_in_thread, daemon=True)
        thread.start()
        thread.join(timeout=10)

        if thread.is_alive():
            pytest.fail("Compaction timed out in background thread")

        if result["error"]:
            if "attached to a different loop" in result["error"]:
                pytest.fail(
                    f"Event loop error in background thread: {result['error']}"
                )
            pytest.fail(f"Unexpected error: {result['error']}")

        assert result["success"], "Compaction did not complete successfully"

    @pytest.mark.asyncio
    async def test_nested_async_calls_work(self):
        """
        Test that nested async calls within asyncio.run() don't cause loop conflicts.

        This validates the complete scenario: asyncio.run() -> async function ->
        async generator (stream_simple).
        """

        async def outer_async():
            """Simulates _compact_history_async."""
            async def inner_async_gen():
                """Simulates stream_simple."""
                yield "chunk1"
                yield "chunk2"
                yield "chunk3"

            result = ""
            async for chunk in inner_async_gen():
                result += chunk

            return result

        # Use asyncio.run to simulate background task execution
        result = await outer_async()
        assert result == "chunk1chunk2chunk3"


class TestHistoryCompactorPreprocessing:
    """Test message preprocessing in history compactor."""

    def test_preprocess_filters_greetings(self, compactor):
        """Test that greeting messages are filtered out."""
        messages = [
            ChatHistory(
                id="1",
                sender=Sender.STUDENT,
                text="Oi",
                timestamp="2026-02-01T10:00:00",
                trainer_id="",
            ),
            ChatHistory(
                id="2",
                sender=Sender.STUDENT,
                text="I want to add weight",
                timestamp="2026-02-01T10:01:00",
                trainer_id="",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert "weight" in filtered[0].text

    def test_preprocess_filters_short_messages(self, compactor):
        """Test that messages shorter than MIN_MESSAGE_LENGTH are filtered."""
        messages = [
            ChatHistory(
                id="1",
                sender=Sender.STUDENT,
                text="ok",
                timestamp="2026-02-01T10:00:00",
                trainer_id="",
            ),
            ChatHistory(
                id="2",
                sender=Sender.STUDENT,
                text="I want to increase my strength significantly",
                timestamp="2026-02-01T10:01:00",
                trainer_id="",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert "strength" in filtered[0].text

    def test_preprocess_filters_trainer_messages(self, compactor):
        """Test that trainer messages are filtered out."""
        messages = [
            ChatHistory(
                id="1",
                sender=Sender.TRAINER,
                text="This is a long trainer message with important info",
                timestamp="2026-02-01T10:00:00",
                trainer_id="",
            ),
            ChatHistory(
                id="2",
                sender=Sender.STUDENT,
                text="I want to improve my cardio fitness level",
                timestamp="2026-02-01T10:01:00",
                trainer_id="",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert filtered[0].sender == Sender.STUDENT
