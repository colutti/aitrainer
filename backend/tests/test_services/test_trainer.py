"""
Tests for the AITrainerBrain service.
"""
import unittest
from unittest.mock import MagicMock, patch

from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.services.trainer import AITrainerBrain


class MockConversationMemory:
    """Mock for ConversationSummaryBufferMemory that returns empty chat history."""
    
    def load_memory_variables(self, inputs):
        return {"chat_history": []}
    
    def save_context(self, inputs, outputs):
        pass


class TestAITrainerBrain(unittest.TestCase):
    """Unit tests for the AITrainerBrain class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        
        # Mock get_conversation_memory to return our mock
        self.mock_conversation_memory = MockConversationMemory()
        self.mock_db.get_conversation_memory.return_value = self.mock_conversation_memory
        
        # Need to mock _llm attribute for the summarization LLM
        self.mock_llm._llm = MagicMock()

        with patch('src.services.trainer.settings') as mock_settings:
            mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
            mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 2000
            self.brain = AITrainerBrain(database=self.mock_db,
                                        llm_client=self.mock_llm,
                                        memory=self.mock_memory)

    def test_send_message_ai_success(self):
        """
        Test send_message_ai with a successful response.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"

        user_profile = UserProfile(email=user_email, gender="Masculino", age=25, weight=70, height=175, 
                                   goal="Muscle gain", goal_type="gain")
        trainer_profile = TrainerProfile(user_email=user_email,
                                         trainer_type="atlas")
        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_memory.search.return_value = {}
        self.mock_llm.stream_with_tools.return_value = iter(["Test response"])

        # Act - send_message_ai returns a generator, so we need to consume it
        response_generator = self.brain.send_message_ai(user_email, user_input, background_tasks=None)
        response = "".join(list(response_generator))

        # Assert
        self.assertEqual(response, "Test response")
        self.mock_db.get_user_profile.assert_called_once_with(user_email)
        self.mock_db.get_trainer_profile.assert_called_once_with(user_email)
        self.mock_db.get_conversation_memory.assert_called_once()
        # Hybrid search makes 2 calls: Critical and Semantic
        self.assertEqual(self.mock_memory.search.call_count, 2)
        self.mock_memory.search.assert_any_call(
            user_id=user_email, 
            query="alergia lesão dor objetivo meta restrição médico cirurgia", 
            limit=5
        )
        self.mock_memory.search.assert_any_call(
            user_id=user_email, 
            query=user_input, 
            limit=5
        )

    def test_send_message_ai_no_user_profile(self):
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
        self.mock_memory.search.return_value = {}
        self.mock_llm.stream_with_tools.return_value = iter(["Response"])

        # Act
        response_generator = self.brain.send_message_ai(user_email, user_input, background_tasks=None)
        response = "".join(list(response_generator))

        # Assert
        self.assertEqual(response, "Response")
        # Verify save_user_profile was called to create the default profile
        self.mock_db.save_user_profile.assert_called_once()

    def test_send_message_ai_no_trainer_profile(self):
        """
        Test send_message_ai creates default trainer profile when not found.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"

        user_profile = UserProfile(email=user_email, gender="Masculino",
                                   age=25, weight=70, height=175,
                                   goal="Muscle gain", goal_type="gain")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = None
        self.mock_memory.search.return_value = {}
        self.mock_llm.stream_with_tools.return_value = iter(["Response"])

        # Act
        response_generator = self.brain.send_message_ai(user_email, user_input, background_tasks=None)
        response = "".join(list(response_generator))

        # Assert
        self.assertEqual(response, "Response")
        # Verify save_trainer_profile was called to create the default profile
        self.mock_db.save_trainer_profile.assert_called_once()



if __name__ == "__main__":
    unittest.main()