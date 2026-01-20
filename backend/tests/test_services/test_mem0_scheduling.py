
import unittest
from unittest.mock import MagicMock, patch
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile

class TestMem0AlwaysCalled(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        self.mock_db.get_conversation_memory.return_value.load_memory_variables.return_value = {"chat_history": []}
        
        # Mock settings
        with patch('src.services.trainer.settings') as mock_settings:
             mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
             mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 2000
             self.brain = AITrainerBrain(database=self.mock_db, llm_client=self.mock_llm, memory=self.mock_memory)

    def test_mem0_task_scheduled_unconditionally(self):
        """
        Verify that Mem0 background task is scheduled regardless of tool usage (simulated).
        Since we removed the conditional logic, this test just checks if add_task is called.
        """
        user_email = "mixed@test.com"
        user_input = "Tenho alergia e mudei meu goal."
        
        # Mock Profile
        self.mock_db.get_user_profile.return_value = UserProfile(
            email=user_email, gender="Masculino", age=30, weight=70, height=170, goal_type="gain"
        )
        self.mock_db.get_trainer_profile.return_value = TrainerProfile(
            user_email=user_email, trainer_type="atlas"
        )
        self.mock_memory.search.return_value = {} # Hybrid search defaults

        # Mock LLM Response (String only, no tool call signal needed as per new architecture)
        self.mock_llm.stream_with_tools.return_value = iter(["Response with tool logic executed inside agent"])
        
        # Mock BackgroundTasks
        mock_bg_tasks = MagicMock()
        
        # Act
        generator = self.brain.send_message_ai(user_email, user_input, background_tasks=mock_bg_tasks)
        limit = list(generator) # Consume generator
        
        # Assert
        # Mem0 should be scheduled
        mock_bg_tasks.add_task.assert_called()
        call_args = mock_bg_tasks.add_task.call_args
        
        # First positional arg is the function
        from src.services.trainer import _add_to_mem0_background
        self.assertEqual(call_args.args[0], _add_to_mem0_background)
        
        # Other args are passed as kwargs in the implementation
        self.assertEqual(call_args.kwargs['user_email'], user_email)
        
        print("\n✅ Assertion Passed: Mem0 task scheduled.")

if __name__ == "__main__":
    unittest.main()
