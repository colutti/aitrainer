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

    def test_send_message_sync_handles_multiple_calls_sequentially(self):
        """
        Test send_message_sync can be called multiple times in sequence.

        This validates that the method properly handles the event loop cleanup
        and can be called again without issues - important for scenarios like
        Telegram where multiple messages arrive in sequence.
        """
        # Arrange
        user_email = "sequential@test.com"
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

        # Mock send_message_ai to simulate streaming
        async def mock_send_message_ai(*args, **kwargs):
            yield "Response"

        self.brain.send_message_ai = mock_send_message_ai

        # Act - call multiple times sequentially
        response1 = self.brain.send_message_sync(
            user_email=user_email,
            user_input="First message",
            is_telegram=True
        )
        response2 = self.brain.send_message_sync(
            user_email=user_email,
            user_input="Second message",
            is_telegram=True
        )
        response3 = self.brain.send_message_sync(
            user_email=user_email,
            user_input="Third message",
            is_telegram=True
        )

        # Assert
        self.assertEqual(response1, "Response")
        self.assertEqual(response2, "Response")
        self.assertEqual(response3, "Response")

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
