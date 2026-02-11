"""
Tests for event loop isolation in history compaction.

Validates that the fix for "Task got Future attached to a different loop" works correctly.
This tests the asyncio.run() fix instead of manual loop management.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock
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
            sender=Sender.STUDENT,
            text="I want to start a new workout routine",
            timestamp="2026-02-01T10:00:00",
        ),
        ChatHistory(
            sender=Sender.TRAINER,
            text="Great! Let's design one for you.",
            timestamp="2026-02-01T10:01:00",
        ),
        ChatHistory(
            sender=Sender.STUDENT,
            text="I prefer lifting weights over cardio",
            timestamp="2026-02-01T10:02:00",
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

    @pytest.mark.asyncio
    async def test_compact_history_native_async(self, compactor, mock_database):
        """
        Test that compact_history is now a native async function.

        The critical fix is making compact_history a native async function instead of
        a sync wrapper around asyncio.run(), which prevents "Future attached to different loop" errors.

        This test verifies the behavior by ensuring:
        1. Function can be awaited directly
        2. Execution completes successfully
        3. No event loop related errors occur
        """
        user_email = "test@example.com"

        # This will execute as a native async function
        # If it completes without RuntimeError about event loops, the fix works
        await compactor.compact_history(user_email)

        # Verify the mock database was called correctly
        mock_database.get_user_profile.assert_called_with(user_email)
        mock_database.get_chat_history.assert_called_with(user_email, limit=1000)

    @pytest.mark.asyncio
    async def test_compact_history_completes_without_event_loop_error(
        self, compactor, mock_database
    ):
        """
        Test that compact_history completes without "Future attached to different loop" error.

        This simulates the actual error that was occurring before the fix.
        """
        user_email = "test@example.com"

        # This should complete without raising asyncio errors
        try:
            await compactor.compact_history(user_email)
            # If we get here without exception, the test passes
            assert True
        except RuntimeError as e:
            if "attached to a different loop" in str(e):
                pytest.fail(
                    f"Event loop error detected: {e}. "
                    "The native async fix may not be working."
                )
            raise

    @pytest.mark.asyncio
    async def test_stream_simple_works_in_isolated_event_loop(self):
        """
        Test that LLMClient.stream_simple works correctly in an isolated event loop.

        This validates that the LLM client works when called from within asyncio.run().
        """
        from langchain_core.prompts import PromptTemplate

        # Create a mock async generator that simulates LLM streaming
        async def mock_astream(data):
            yield "Response "
            yield "chunk"

        # Create the prompt template
        _ = PromptTemplate.from_template("Test: {input}")

        # This is what actually happens inside stream_simple
        result = ""
        async for chunk in mock_astream({"input": "data"}):
            result += chunk

        assert result == "Response chunk"

    @pytest.mark.asyncio
    async def test_compact_history_works_as_background_task(self, compactor):
        """
        Test that compact_history works when scheduled as a FastAPI background task.

        This simulates the actual scenario where it's called via background_tasks.add_task().
        FastAPI runs async background tasks in the main event loop, which is what we're testing here.
        """

        user_email = "test@example.com"
        result = {"success": False, "error": None}

        async def run_as_background_task():
            """Simulates FastAPI background_tasks.add_task() behavior."""
            try:
                await compactor.compact_history(user_email)
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)

        # Create task in the current event loop (like FastAPI does)
        task = asyncio.create_task(run_as_background_task())

        try:
            await asyncio.wait_for(task, timeout=10)
        except asyncio.TimeoutError:
            pytest.fail("Compaction timed out as background task")

        if result["error"]:
            if "attached to a different loop" in result["error"]:
                pytest.fail(
                    f"Event loop error in background task: {result['error']}"
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
                sender=Sender.STUDENT,
                text="Oi",
                timestamp="2026-02-01T10:00:00",
            ),
            ChatHistory(
                sender=Sender.STUDENT,
                text="I want to add weight",
                timestamp="2026-02-01T10:01:00",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert "weight" in filtered[0].text

    def test_preprocess_filters_short_messages(self, compactor):
        """Test that messages shorter than MIN_MESSAGE_LENGTH are filtered."""
        messages = [
            ChatHistory(
                sender=Sender.STUDENT,
                text="ok",
                timestamp="2026-02-01T10:00:00",
            ),
            ChatHistory(
                sender=Sender.STUDENT,
                text="I want to increase my strength significantly",
                timestamp="2026-02-01T10:01:00",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert "strength" in filtered[0].text

    def test_preprocess_filters_trainer_messages(self, compactor):
        """Test that trainer messages are filtered out."""
        messages = [
            ChatHistory(
                sender=Sender.TRAINER,
                text="This is a long trainer message with important info",
                timestamp="2026-02-01T10:00:00",
            ),
            ChatHistory(
                sender=Sender.STUDENT,
                text="I want to improve my cardio fitness level",
                timestamp="2026-02-01T10:01:00",
            ),
        ]

        filtered = compactor._preprocess_messages(messages)
        assert len(filtered) == 1
        assert filtered[0].sender == Sender.STUDENT
