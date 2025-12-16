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
                                    llm=self.mock_llm,
                                    memory=self.mock_memory)

    @patch("src.services.trainer.StrOutputParser", new=MockRunnable)
    def test_send_message_ai_success(self):
        """
        Test send_message_ai with a successful response.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        # session_id is removed from here

        user_profile = UserProfile(email=user_email, gender="Masculino",
                                   age=25, weight=70, height=175,
                                   goal="Muscle gain")
        trainer_profile = TrainerProfile(user_email=user_email,
                                         name="Test Trainer",
                                         humour="Amigavel",
                                         gender="Masculino",
                                         style="Científico")
        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_db.get_chat_history.return_value = []
        self.mock_memory.search.return_value = {}

        # Act
        response = self.brain.send_message_ai(user_email, user_input)

        # Assert
        self.assertEqual(response, "Test response")
        self.mock_db.get_user_profile.assert_called_once_with(user_email)
        self.mock_db.get_trainer_profile.assert_called_once_with(user_email)
        self.mock_db.get_chat_history.assert_called_once_with(user_email) # Changed from session_id
        self.mock_memory.search.assert_called_once_with(user_id=user_email,
                                                       query=user_input)
    def test_send_message_ai_no_user_profile(self):
        """
        Test send_message_ai when user profile is not found.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        # session_id is removed from here

        self.mock_db.get_user_profile.return_value = None

        # Act & Assert
        with self.assertRaises(ValueError):
            self.brain.send_message_ai(user_email, user_input)

    def test_send_message_ai_no_trainer_profile(self):
        """
        Test send_message_ai when trainer profile is not found.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        # session_id is removed from here

        user_profile = UserProfile(email=user_email, gender="Masculino",
                                   age=25, weight=70, height=175,
                                   goal="Muscle gain")

        self.mock_db.get_user_profile.return_value = user_profile
        self.mock_db.get_trainer_profile.return_value = None

        # Act & Assert
        with self.assertRaises(ValueError):
            self.brain.send_message_ai(user_email, user_input)