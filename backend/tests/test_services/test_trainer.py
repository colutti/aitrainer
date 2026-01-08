"""
This module contains unit tests for the AITrainerBrain service.
"""
import unittest
from unittest.mock import MagicMock, patch

from langchain_core.runnables import Runnable

from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile


class MockRunnable(Runnable):
    """
    A mock runnable class for testing purposes.
    """
    def invoke(self, *args, **kwargs): # pylint: disable=unused-argument
        """
        Mock invoke method.
        """
        return iter(["Test response"])

    def stream(self, *args, **kwargs): # pylint: disable=unused-argument
        """
        Mock stream method.
        """
        return iter(["Test response"])


class TestAITrainerBrain(unittest.TestCase):
    """
    Tests for the AITrainerBrain service.
    """
    # pylint: disable=invalid-name
    def setUp(self):
        """
        Set up mocks for AITrainerBrain dependencies.
        """
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
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

        user_profile = UserProfile(email=user_email, gender="Masculino",
                                   age=25, weight=70, height=175,
                                   goal="Muscle gain")
        trainer_profile = TrainerProfile(user_email=user_email,
                                         name="Test Trainer",
                                         gender="Masculino",
                                         style="Científico")
        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_db.get_chat_history.return_value = []
        self.mock_memory.search.return_value = {}
        self.mock_llm.stream_with_tools.return_value = iter(["Test response"])

        # Act - send_message_ai returns a generator, so we need to consume it
        response_generator = self.brain.send_message_ai(user_email, user_input, background_tasks=None)
        response = "".join(list(response_generator))

        # Assert
        self.assertEqual(response, "Test response")
        self.mock_db.get_user_profile.assert_called_once_with(user_email)
        self.mock_db.get_trainer_profile.assert_called_once_with(user_email)
        self.mock_db.get_chat_history.assert_called_once_with(user_email)
        self.mock_memory.search.assert_called_once_with(user_id=user_email,
                                                       query=user_input)
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
            user_email=user_email, name="Test", gender="Masculino", style="Científico"
        )
        self.mock_db.get_chat_history.return_value = []
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
                                   goal="Muscle gain")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = None
        self.mock_db.get_chat_history.return_value = []
        self.mock_memory.search.return_value = {}
        self.mock_llm.stream_with_tools.return_value = iter(["Response"])

        # Act
        response_generator = self.brain.send_message_ai(user_email, user_input, background_tasks=None)
        response = "".join(list(response_generator))

        # Assert
        self.assertEqual(response, "Response")
        # Verify save_trainer_profile was called to create the default profile
        self.mock_db.save_trainer_profile.assert_called_once()