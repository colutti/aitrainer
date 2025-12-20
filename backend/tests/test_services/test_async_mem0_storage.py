"""
Unit tests for async Mem0 storage functionality.
"""
import unittest
from unittest.mock import MagicMock, patch

from fastapi import BackgroundTasks
from langchain_core.runnables import Runnable

from src.services.trainer import AITrainerBrain, _add_to_mem0_background
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile


class MockRunnable(Runnable):
    """
    A mock runnable class for testing purposes.
    """
    def invoke(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Mock invoke method.
        """
        return iter(["Test response"])

    def stream(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Mock stream method.
        """
        return iter(["Test response"])


class TestAsyncMem0Storage(unittest.TestCase):
    """
    Tests for async Mem0 storage with BackgroundTasks.
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

    def test_add_to_mongo_history_only_saves_to_mongodb(self):
        """
        Test that _add_to_mongo_history only saves to MongoDB, not Mem0.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        response_text = "Hi there!"

        # Act
        self.brain._add_to_mongo_history(user_email, user_input, response_text)

        # Assert
        # MongoDB should be called twice (user message + AI message)
        self.assertEqual(self.mock_db.add_to_history.call_count, 2)
        # Mem0 should NOT be called
        self.mock_memory.add.assert_not_called()

    def test_add_to_mem0_background_success(self):
        """
        Test that _add_to_mem0_background successfully adds to Mem0.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        response_text = "Hi there!"

        # Act
        _add_to_mem0_background(
            memory=self.mock_memory,
            user_email=user_email,
            user_input=user_input,
            response_text=response_text
        )

        # Assert
        expected_messages = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ]
        self.mock_memory.add.assert_called_once_with(expected_messages, user_id=user_email)

    @patch("src.services.trainer.logger")
    def test_add_to_mem0_background_error_handling(self, mock_logger):
        """
        Test that _add_to_mem0_background handles errors gracefully.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        response_text = "Hi there!"
        self.mock_memory.add.side_effect = Exception("Mem0 connection failed")

        # Act - should not raise exception
        _add_to_mem0_background(
            memory=self.mock_memory,
            user_email=user_email,
            user_input=user_input,
            response_text=response_text
        )

        # Assert - error should be logged
        mock_logger.error.assert_called_once()
        self.assertIn("Failed to add memory to Mem0", str(mock_logger.error.call_args))

    @patch("src.services.trainer.StrOutputParser", new=MockRunnable)
    def test_send_message_ai_schedules_background_task(self):
        """
        Test that send_message_ai schedules Mem0 storage as a background task.
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        
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
        
        # Mock BackgroundTasks
        mock_background_tasks = MagicMock(spec=BackgroundTasks)

        # Act
        list(self.brain.send_message_ai(user_email, user_input, mock_background_tasks))

        # Assert
        # MongoDB should be called (synchronous)
        self.assertEqual(self.mock_db.add_to_history.call_count, 2)
        
        # Background task should be scheduled
        mock_background_tasks.add_task.assert_called_once()
        
        # Verify the background task was called with correct function and parameters
        call_args = mock_background_tasks.add_task.call_args
        self.assertEqual(call_args[0][0], _add_to_mem0_background)
        self.assertEqual(call_args[1]["memory"], self.mock_memory)
        self.assertEqual(call_args[1]["user_email"], user_email)
        self.assertEqual(call_args[1]["user_input"], user_input)

    @patch("src.services.trainer.StrOutputParser", new=MockRunnable)
    def test_send_message_ai_without_background_tasks(self):
        """
        Test that send_message_ai works without BackgroundTasks (backward compatibility).
        """
        # Arrange
        user_email = "test@test.com"
        user_input = "Hello"
        
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

        # Act - call without background_tasks parameter
        list(self.brain.send_message_ai(user_email, user_input, background_tasks=None))

        # Assert
        # MongoDB should still be called
        self.assertEqual(self.mock_db.add_to_history.call_count, 2)
        # Mem0 should NOT be called (no background task)
        self.mock_memory.add.assert_not_called()


if __name__ == "__main__":
    unittest.main()
