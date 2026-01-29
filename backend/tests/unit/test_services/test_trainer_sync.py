"""
Tests for the AITrainerBrain.send_message_sync() method.

This test module focuses on the synchronous version of send_message_ai,
which is used by the Telegram bot. It tests the fallback behavior with
nest_asyncio when an event loop is already running.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, patch, AsyncMock

from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.services.trainer import AITrainerBrain


class MockConversationMemory:
    """Mock for ConversationSummaryBufferMemory that returns empty chat history."""

    def load_memory_variables(self, inputs):
        return {"chat_history": []}

    def save_context(self, inputs, outputs):
        pass


class TestAITrainerBrainSync(unittest.TestCase):
    """Unit tests for the AITrainerBrain.send_message_sync() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()

        # Mock get_conversation_memory to return our mock
        self.mock_conversation_memory = MockConversationMemory()
        self.mock_db.get_conversation_memory.return_value = (
            self.mock_conversation_memory
        )

        # Need to mock _llm attribute for the summarization LLM
        self.mock_llm._llm = MagicMock()

        with (
            patch("src.services.trainer.settings") as mock_settings,
            patch("src.services.trainer.HistoryCompactor") as mock_compactor_cls,
        ):
            self.mock_compactor = mock_compactor_cls.return_value
            mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
            mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 2000
            mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 10

            # Mock get_window_memory to return our mock
            self.mock_conversation_memory = MockConversationMemory()
            self.mock_db.get_window_memory.return_value = self.mock_conversation_memory

            self.brain = AITrainerBrain(
                database=self.mock_db, llm_client=self.mock_llm, memory=self.mock_memory
            )

            # Ensure compactor was instantiated
            mock_compactor_cls.assert_called_with(self.mock_db, self.mock_llm)

    def test_send_message_sync_returns_complete_response(self):
        """
        Test send_message_sync returns a complete response string.

        This tests the basic functionality where asyncio.run() succeeds.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello AI"

        user_profile = UserProfile(
            email=user_email,
            gender="Masculino",
            age=25,
            weight=70,
            height=175,
            goal="Muscle gain",
            goal_type="gain",
            weekly_rate=0.5,
        )
        trainer_profile = TrainerProfile(user_email=user_email, trainer_type="atlas")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_memory.search.return_value = {}

        # Mock send_message_ai to yield chunks
        async def mock_send_message_ai(*args, **kwargs):
            yield "Hello "
            yield "from "
            yield "AI"

        self.brain.send_message_ai = mock_send_message_ai

        # Act
        response = self.brain.send_message_sync(
            user_email=user_email,
            user_input=user_input,
            is_telegram=True
        )

        # Assert
        self.assertEqual(response, "Hello from AI")
        self.assertIsInstance(response, str)

    def test_send_message_sync_with_running_loop_uses_nest_asyncio(self):
        """
        Test send_message_sync falls back to nest_asyncio when event loop is running.

        This reproduces the Telegram scenario where the bot runs in an existing
        event loop. The method should handle RuntimeError and use nest_asyncio.apply().
        """
        # Arrange
        user_email = "telegram@test.com"
        user_input = "Training message from Telegram"

        user_profile = UserProfile(
            email=user_email,
            gender="Feminino",
            age=30,
            weight=60,
            height=165,
            goal="Fat loss",
            goal_type="lose",
            weekly_rate=0.5,
        )
        trainer_profile = TrainerProfile(user_email=user_email, trainer_type="luna")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_memory.search.return_value = {}

        # Mock send_message_ai
        async def mock_send_message_ai(*args, **kwargs):
            yield "Response "
            yield "chunk"

        self.brain.send_message_ai = mock_send_message_ai

        # Mock asyncio.run to raise RuntimeError (simulating running loop)
        # Then mock the fallback path
        with patch("src.services.trainer.asyncio.run") as mock_run:
            mock_run.side_effect = RuntimeError("asyncio.run() cannot be called from a running event loop")

            # Mock asyncio.get_event_loop and loop.run_until_complete
            mock_loop = MagicMock()
            mock_loop.is_running.return_value = True

            # Create a real async function result
            async def dummy():
                yield "Response "
                yield "chunk"

            # Mock run_until_complete to collect the async generator
            def collect_response():
                async def inner():
                    result = []
                    async for chunk in dummy():
                        result.append(chunk)
                    return "".join(result)

                # Create a new event loop, run it, close it
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    response = new_loop.run_until_complete(inner())
                    return response
                finally:
                    new_loop.close()

            mock_loop.run_until_complete.side_effect = collect_response

            with patch("src.services.trainer.asyncio.get_event_loop", return_value=mock_loop):
                with patch("src.services.trainer.nest_asyncio") as mock_nest_asyncio:
                    # Act
                    response = self.brain.send_message_sync(
                        user_email=user_email,
                        user_input=user_input,
                        is_telegram=True
                    )

                    # Assert
                    self.assertEqual(response, "Response chunk")
                    # Verify nest_asyncio.apply() was called as a fallback
                    mock_nest_asyncio.apply.assert_called_once()

    def test_send_message_sync_with_is_telegram_flag(self):
        """
        Test send_message_sync passes is_telegram flag to send_message_ai.
        """
        # Arrange
        user_email = "tg@test.com"
        user_input = "Message"

        user_profile = UserProfile(
            email=user_email,
            gender="Masculino",
            age=25,
            weight=70,
            height=175,
            goal="Muscle gain",
            goal_type="gain",
            weekly_rate=0.5,
        )
        trainer_profile = TrainerProfile(user_email=user_email, trainer_type="atlas")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_memory.search.return_value = {}

        call_kwargs = {}

        async def mock_send_message_ai(*args, **kwargs):
            call_kwargs.update(kwargs)
            yield "Response"

        self.brain.send_message_ai = mock_send_message_ai

        # Act
        response = self.brain.send_message_sync(
            user_email=user_email,
            user_input=user_input,
            is_telegram=True
        )

        # Assert
        self.assertEqual(response, "Response")
        self.assertTrue(call_kwargs.get("is_telegram"))

    def test_send_message_sync_collects_all_chunks(self):
        """
        Test send_message_sync correctly collects all chunks from async generator.
        """
        # Arrange
        user_email = "chunk@test.com"
        user_input = "Multi-chunk test"

        user_profile = UserProfile(
            email=user_email,
            gender="Masculino",
            age=25,
            weight=70,
            height=175,
            goal="Muscle gain",
            goal_type="gain",
            weekly_rate=0.5,
        )
        trainer_profile = TrainerProfile(user_email=user_email, trainer_type="atlas")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_memory.search.return_value = {}

        # Mock with many chunks
        async def mock_send_message_ai(*args, **kwargs):
            chunks = [
                "Training ",
                "your ",
                "strength ",
                "is ",
                "important. ",
                "Let's ",
                "work ",
                "on ",
                "your ",
                "goal!"
            ]
            for chunk in chunks:
                yield chunk

        self.brain.send_message_ai = mock_send_message_ai

        # Act
        response = self.brain.send_message_sync(
            user_email=user_email,
            user_input=user_input
        )

        # Assert
        expected = "Training your strength is important. Let's work on your goal!"
        self.assertEqual(response, expected)


if __name__ == "__main__":
    unittest.main()
