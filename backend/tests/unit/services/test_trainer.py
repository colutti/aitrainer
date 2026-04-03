"""
Tests for the AITrainerBrain service.
"""

import unittest
from unittest.mock import MagicMock, patch

from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.services.trainer import AITrainerBrain


class MockConversationMemory:
    """Mock for ConversationSummaryBufferMemory that returns empty chat history."""

    def load_memory_variables(self, inputs):
        return {"chat_history": []}

    def save_context(self, inputs, outputs):
        pass


class TestAITrainerBrain(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the AITrainerBrain class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()

        # Mock get_conversation_memory to return our mock
        self.mock_conversation_memory = MockConversationMemory()
        self.mock_db.get_conversation_memory.return_value = (
            self.mock_conversation_memory
        )

        # Need to mock _llm attribute for the summarization LLM
        self.mock_llm._llm = MagicMock()

        with patch("src.services.trainer.settings") as mock_settings:
            mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
            mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 10

            # Mock get_window_memory to return our mock
            self.mock_conversation_memory = MockConversationMemory()
            self.mock_db.get_window_memory.return_value = self.mock_conversation_memory

            self.brain = AITrainerBrain(
                database=self.mock_db, llm_client=self.mock_llm
            )

    async def test_send_message_ai_success(self):
        """
        Test send_message_ai with a successful response.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"

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
        # Memory search removed with Mem0
        
        # Mock async iterator for stream_with_tools
        async def mock_stream(*args, **kwargs):
            yield "Test response"
            
        self.mock_llm.stream_with_tools = mock_stream

        # Act
        response_chunks = []
        async for chunk in self.brain.send_message_ai(
            user_email, user_input, background_tasks=None
        ):
            response_chunks.append(chunk)
        response = "".join(response_chunks)

        # Assert
        self.assertEqual(response, "Test response")
        self.mock_db.get_user_profile.assert_called_once_with(user_email)
        self.mock_db.get_trainer_profile.assert_called_once_with(user_email)
        self.mock_db.get_window_memory.assert_called_once()
        # POC: Memory injection removed, AI now manages memories via tools
        # No automatic memory retrieval happens
        # Memory search removed with Mem0

    async def test_send_message_ai_no_user_profile(self):
        """
        Test send_message_ai creates default user profile when not found.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"

        self.mock_db.get_user_profile.return_value = None
        # Should return a default trainer profile to proceed
        self.mock_db.get_trainer_profile.return_value = TrainerProfile(
            user_email=user_email, trainer_type="atlas"
        )
        # Memory search removed with Mem0
        
        async def mock_stream(*args, **kwargs):
            yield "Response"
        self.mock_llm.stream_with_tools = mock_stream

        # Act
        response_chunks = []
        async for chunk in self.brain.send_message_ai(
            user_email, user_input, background_tasks=None
        ):
            response_chunks.append(chunk)
        response = "".join(response_chunks)

        # Assert
        self.assertEqual(response, "Response")
        # Verify save_user_profile was called to create the default profile
        self.mock_db.save_user_profile.assert_called_once()

    async def test_send_message_ai_no_trainer_profile(self):
        """
        Test send_message_ai creates default trainer profile when not found.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"

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

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = None
        # Memory search removed with Mem0
        
        async def mock_stream(*args, **kwargs):
            yield "Response"
        self.mock_llm.stream_with_tools = mock_stream

        # Act
        response_chunks = []
        async for chunk in self.brain.send_message_ai(
            user_email, user_input, background_tasks=None
        ):
            response_chunks.append(chunk)
        response = "".join(response_chunks)

        # Assert
        self.assertEqual(response, "Response")
        # Verify save_trainer_profile was called to create the default profile
        self.mock_db.save_trainer_profile.assert_called_once()

    def test_get_chat_history_sanitizes_only_trainer_internal_tags(self):
        """
        Trainer messages from old history should have only protocol wrappers removed.
        Student content must remain unchanged.
        """
        user_email = "test@test.com"
        self.mock_db.get_chat_history.return_value = [
            ChatHistory(
                text='<msg data="03/04" hora="14:57"><treinador name="Atlas">Resposta antiga</treinador></msg>',
                sender=Sender.TRAINER,
                timestamp="2026-04-03T14:57:00",
            ),
            ChatHistory(
                text='Dados do usuário: <msg data="arquivo.csv">linha 1</msg>',
                sender=Sender.STUDENT,
                timestamp="2026-04-03T14:58:00",
            ),
        ]

        messages = self.brain.get_chat_history(user_email, limit=20, offset=0)

        assert messages[0].text == "Resposta antiga"
        assert messages[1].text == 'Dados do usuário: <msg data="arquivo.csv">linha 1</msg>'


if __name__ == "__main__":
    unittest.main()
