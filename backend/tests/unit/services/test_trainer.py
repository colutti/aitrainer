"""Tests for the AITrainerBrain service."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.services.trainer import AITrainerBrain


class MockConversationMemory:
    """Mock memory object used by get_window_memory."""

    def load_memory_variables(self, _inputs):
        return {"chat_history": []}


class TestAITrainerBrain(unittest.IsolatedAsyncioTestCase):
    """Unit tests for AITrainerBrain."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_llm = MagicMock()

        self.settings_patcher = patch("src.services.trainer.settings")
        self.to_thread_patcher = patch(
            "src.services.trainer.asyncio.to_thread",
            new=AsyncMock(side_effect=lambda func, *args, **kwargs: func(*args, **kwargs)),
        )
        mock_settings = self.settings_patcher.start()
        self.to_thread_patcher.start()
        self.addCleanup(self.settings_patcher.stop)
        self.addCleanup(self.to_thread_patcher.stop)
        mock_settings.MAX_LONG_TERM_MEMORY_MESSAGES = 20
        mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 10
        mock_settings.AI_TRAINER_THREADPOOL_WORKERS = 4
        mock_settings.OPENROUTER_CHAT_MODEL = "google/gemini-3.5-flash"
        mock_settings.LLM_STREAM_TIMEOUT_SECONDS = 120

        profile = UserProfile(
            email="test@test.com",
            gender="Masculino",
            age=30,
            weight=80,
            height=175,
            goal="ganhar massa",
            goal_type="gain",
            weekly_rate=0.5,
        )
        trainer_profile = TrainerProfile(user_email="test@test.com", trainer_type="atlas")
        trainer_profile.preferred_language = "pt-BR"

        self.mock_db.get_user_profile.return_value = profile
        self.mock_db.get_trainer_profile.return_value = trainer_profile
        self.mock_db.get_window_memory.return_value = MockConversationMemory()
        self.mock_db.get_plan.return_value = None

        self.brain = AITrainerBrain(database=self.mock_db, llm_client=self.mock_llm)
        self.tdee_patcher = patch(
            "src.services.trainer.AdaptiveTDEEService.calculate_tdee",
            return_value={
                "tdee": 2200,
                "daily_target": 2000,
                "calories": 2000,
                "protein_g": 150,
                "carbs_g": 200,
                "fat_g": 60,
            },
        )
        self.events_patcher = patch(
            "src.services.trainer.EventRepository.get_active_events",
            return_value=[],
        )
        self.tdee_patcher.start()
        self.events_patcher.start()
        self.addCleanup(self.tdee_patcher.stop)
        self.addCleanup(self.events_patcher.stop)
        self.brain.get_tools = MagicMock(return_value=[])
        self.brain.check_message_limits = MagicMock(return_value=False)
        self.brain.prompt_builder.build_input_data = MagicMock(
            return_value={
                "chat_history": [],
                "user_message": "<msg>oi</msg>",
                "runtime_context": {"session": {"channel": "app"}},
            }
        )
        self.brain.prompt_builder.get_prompt_template = MagicMock(return_value=MagicMock())

    async def test_send_message_ai_streams_text_from_llm(self):
        """send_message_ai should stream plain text chunks in legacy single-model flow."""

        async def _stream_with_tools(**_kwargs):
            yield "resposta "
            yield "final"

        self.mock_llm.stream_with_tools = _stream_with_tools

        chunks = []
        async for chunk in self.brain.send_message_ai("test@test.com", "oi"):
            chunks.append(chunk)

        self.assertEqual("".join(chunks), "resposta final")
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    async def test_send_message_ai_uses_configured_chat_model(self):
        """send_message_ai must call stream_with_tools with OPENROUTER_CHAT_MODEL."""
        captured = {}

        async def _stream_with_tools(**kwargs):
            captured.update(kwargs)
            yield "ok"

        self.mock_llm.stream_with_tools = _stream_with_tools
        async for _ in self.brain.send_message_ai("test@test.com", "oi"):
            pass

        self.assertEqual(captured["model_override"], "google/gemini-3.5-flash")
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    def test_get_chat_history_sanitizes_only_trainer_internal_tags(self):
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

    def test_enforce_plan_update_truth_policy_blocks_false_success(self):
        response = AITrainerBrain.enforce_plan_update_truth_policy(
            final_response="Atualizado com sucesso!",
            tool_events=[
                {
                    "type": "tool_result",
                    "tool_name": "update_plan_section",
                    "content": '{"status":"validation_error","saved":false,"plan_materially_changed":false}',
                }
            ],
            user_locale="pt-BR",
        )

        assert "Nao consegui aplicar uma atualizacao material no seu plano" in response

    def test_enforce_plan_update_truth_policy_preserves_response_on_material_change(self):
        original = "Plano atualizado com sucesso."
        response = AITrainerBrain.enforce_plan_update_truth_policy(
            final_response=original,
            tool_events=[
                {
                    "type": "tool_result",
                    "tool_name": "update_plan_section",
                    "content": '{"status":"success","saved":true,"plan_materially_changed":true}',
                }
            ],
            user_locale="pt-BR",
        )

        assert response == original


if __name__ == "__main__":
    unittest.main()
