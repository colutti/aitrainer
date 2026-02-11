import unittest
from unittest.mock import MagicMock, patch
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile


class TestMem0AlwaysCalled(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()
        self.mock_memory = MagicMock()
        self.mock_db.get_window_memory.return_value.load_memory_variables.return_value = {
            "chat_history": []
        }

        # Mock settings
        with (
            patch("src.services.trainer.settings") as mock_settings,
            patch("src.services.trainer.HistoryCompactor"),
        ):
            mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
            mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 2000
            mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 10
            self.brain = AITrainerBrain(
                database=self.mock_db, llm_client=self.mock_llm, memory=self.mock_memory
            )

    async def test_mem0_task_scheduled_unconditionally(self):
        """
        Verify that Mem0 background task is scheduled regardless of tool usage (simulated).
        Since we removed the conditional logic, this test just checks if add_task is called.
        """
        user_email = "mixed@test.com"
        user_input = "Tenho alergia e mudei meu goal."

        # Mock Profile
        self.mock_db.get_user_profile.return_value = UserProfile(
            email=user_email,
            gender="Masculino",
            age=30,
            weight=70,
            height=170,
            goal_type="gain",
        )
        self.mock_db.get_trainer_profile.return_value = TrainerProfile(
            user_email=user_email, trainer_type="atlas"
        )
        self.mock_memory.search.return_value = {}  # Hybrid search defaults

        # Mock LLM Response
        async def mock_stream(*args, **kwargs):
            yield "Response with tool logic executed inside agent"
        self.mock_llm.stream_with_tools = mock_stream

        # Mock BackgroundTasks
        mock_bg_tasks = MagicMock()

        # Act
        async for chunk in self.brain.send_message_ai(
            user_email, user_input, background_tasks=mock_bg_tasks
        ):
            pass

        # Assert
        # Mem0 should be scheduled
        mock_bg_tasks.add_task.assert_called()
        # Verify Mem0 task is in one of the calls
        from src.services.trainer import _add_to_mem0_background

        mem0_call_found = False
        for call in mock_bg_tasks.add_task.call_args_list:
            # Check if this call is the Mem0 task
            if call.args[0] == _add_to_mem0_background:
                mem0_call_found = True
                self.assertEqual(call.kwargs["user_email"], user_email)
                break

        self.assertTrue(mem0_call_found, "Mem0 background task was not scheduled")


if __name__ == "__main__":
    unittest.main()
