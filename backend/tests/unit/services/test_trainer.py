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
        self.mock_db.get_plan.return_value = None

        # Need to mock _llm attribute for the summarization LLM
        self.mock_llm._llm = MagicMock()

        self.settings_patcher = patch("src.services.trainer.settings")
        mock_settings = self.settings_patcher.start()
        self.addCleanup(self.settings_patcher.stop)
        mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
        mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 10
        mock_settings.AI_TRAINER_THREADPOOL_WORKERS = 4
        mock_settings.LANGSMITH_ENVIRONMENT = "dev"
        mock_settings.ENABLE_EXPERIMENTAL_CONVERSATION_GRAPH = False

        # Mock get_window_memory to return our mock
        self.mock_conversation_memory = MockConversationMemory()
        self.mock_db.get_window_memory.return_value = self.mock_conversation_memory

        self.brain = AITrainerBrain(
            database=self.mock_db, llm_client=self.mock_llm
        )
        self.brain.get_tools = MagicMock(return_value=[])
        self.brain.prompt_builder.build_input_data = MagicMock(
            return_value={
                "user_profile": "perfil",
                "trainer_profile": "treinador",
                "formatted_history": "",
                "current_date": "2026-05-01",
                "agenda_section": "",
                "plan_section": "",
                "metabolism_section": "",
                "runtime_context": {"session": {"channel": "app"}, "plan": {}},
            }
        )
        self.brain.prompt_builder.get_prompt_template = MagicMock(return_value=MagicMock())

        self.tdee_patcher = patch("src.services.trainer.AdaptiveTDEEService")
        mock_tdee_cls = self.tdee_patcher.start()
        self.addCleanup(self.tdee_patcher.stop)
        mock_tdee_cls.return_value.calculate_tdee.return_value = {
            "tdee": 2400,
            "daily_target": 2200,
            "goal_type": "maintain",
            "goal_weekly_rate": 0.0,
            "confidence": "medium",
            "macro_targets": {"protein_g": 160, "carbs_g": 180, "fat_g": 60},
        }

        self.event_repo_patcher = patch("src.services.trainer.EventRepository")
        mock_event_repo_cls = self.event_repo_patcher.start()
        self.addCleanup(self.event_repo_patcher.stop)
        mock_event_repo_cls.return_value.get_active_events.return_value = []

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

    @patch("src.services.trainer.settings")
    def test_graph_debug_trace_roundtrip_is_dev_only(self, mock_settings):
        mock_settings.LANGSMITH_ENVIRONMENT = "dev"

        trace = {
            "user_email": "test@test.com",
            "request_id": "req-1",
            "conversation_id": "test@test.com",
            "turn_id": "turn-1",
            "channel": "app",
            "status": "success",
            "error": None,
            "started_at": "2026-05-01T10:00:00.000Z",
            "ended_at": "2026-05-01T10:00:01.000Z",
            "duration_ms": 1000,
            "intent": "general",
            "security_status": "safe",
            "plan_needs_revision": False,
            "tools_called": [],
            "persistence_actions": [],
            "final_response": "ok",
            "technical_response": "ok",
            "node_outputs": {},
            "nodes": [],
        }

        self.brain.store_graph_debug_trace("turn-1", trace)
        stored = self.brain.get_graph_debug_trace("turn-1", "test@test.com")
        assert stored is not None
        assert stored["turn_id"] == "turn-1"
        assert stored["status"] == "success"
        assert self.brain.get_graph_debug_trace("turn-1", "other@test.com") is None

    @patch("src.services.trainer.settings")
    def test_graph_debug_trace_disabled_outside_dev(self, mock_settings):
        mock_settings.LANGSMITH_ENVIRONMENT = "prod"

        self.brain.store_graph_debug_trace(
            "turn-1",
            {
                "user_email": "test@test.com",
                "turn_id": "turn-1",
                "status": "success",
                "nodes": [],
            },
        )
        assert self.brain.get_graph_debug_trace("turn-1", "test@test.com") is None


if __name__ == "__main__":
    unittest.main()
