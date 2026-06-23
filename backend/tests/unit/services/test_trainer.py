"""Tests for the AITrainerBrain service."""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from langchain_core.messages import AIMessage

from src.api.models.chat_history import ChatHistory
from src.api.models.plan import PlanPromptContext
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.services.prompt_builder import PromptBuilder
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
        """send_message_ai should emit structured SSE events with final text."""

        async def _stream_with_tools(**kwargs):
            if kwargs.get("tools"):
                yield {"type": "tool_result", "tool_name": "get_plan", "content": '{"status":"ACTIVE_PLAN"}'}
                yield "rascunho interno"
                yield {"type": "tools_summary", "tools_called": ["get_plan"]}
                return
            yield "resposta "
            yield "final"

        self.mock_llm.stream_with_tools = _stream_with_tools

        chunks = []
        async for chunk in self.brain.send_message_ai("test@test.com", "oi"):
            chunks.append(chunk)

        payload = "".join(chunks)
        self.assertIn("event: status", payload)
        self.assertIn('"stage":"using_tools"', payload)
        self.assertIn('"stage":"writing_reply"', payload)
        self.assertIn("event: delta", payload)
        self.assertIn("event: done", payload)
        self.assertIn('"text":"resposta final"', payload)
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    async def test_send_message_ai_uses_configured_chat_model(self):
        """send_message_ai must call stream_with_tools with OPENROUTER_CHAT_MODEL."""
        captured = []

        async def _stream_with_tools(**kwargs):
            captured.append(kwargs)
            if kwargs.get("tools"):
                yield {"type": "tools_summary", "tools_called": []}
                return
            yield "ok"

        self.mock_llm.stream_with_tools = _stream_with_tools
        async for _ in self.brain.send_message_ai("test@test.com", "oi"):
            pass

        self.assertEqual(captured[0]["model_override"], "google/gemini-3.5-flash")
        self.assertEqual(captured[1]["model_override"], "google/gemini-3.5-flash")
        self.assertEqual(captured[0]["provider_sort"], "throughput")
        self.assertEqual(captured[1]["provider_sort"], "latency")
        self.assertEqual(captured[0]["parallel_tool_calls"], False)
        self.assertEqual(captured[1]["tools"], [])
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    async def test_send_message_ai_does_not_persist_stream_errors(self):
        """A provider error is shown to the user but must not enter chat history."""

        async def _stream_with_tools(**_kwargs):
            yield {"type": "stream_error", "error_type": "ValueError"}
            yield {"type": "tools_summary", "tools_called": []}

        self.mock_llm.stream_with_tools = _stream_with_tools

        chunks = []
        async for chunk in self.brain.send_message_ai("test@test.com", "oi"):
            chunks.append(chunk)

        payload = "".join(chunks)
        self.assertIn("event: error", payload)
        self.mock_db.add_to_history.assert_not_called()
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    async def test_send_message_ai_uses_20_message_window(self):
        async def _stream_with_tools(**kwargs):
            if kwargs.get("tools"):
                yield {"type": "tools_summary", "tools_called": []}
                return
            yield "ok"

        self.mock_llm.stream_with_tools = _stream_with_tools
        with patch("src.services.trainer.settings.MAX_SHORT_TERM_MEMORY_MESSAGES", 20):
            async for _ in self.brain.send_message_ai("test@test.com", "oi"):
                pass

        self.mock_db.get_window_memory.assert_any_call(
            session_id="test@test.com",
            k=20,
        )
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

    def test_format_sse_event_serializes_payload(self):
        chunk = AITrainerBrain.format_sse_event(
            "done",
            {"text": "oi", "persisted": True},
        )

        self.assertEqual(
            chunk,
            'event: done\ndata: {"text":"oi","persisted":true}\n\n',
        )

    def test_summarize_tool_events_marks_material_plan_change(self):
        summary = AITrainerBrain.summarize_tool_events(
            [
                {
                    "tool_name": "update_plan_section",
                    "content": json.dumps(
                        {
                            "status": "success",
                            "saved": True,
                            "plan_materially_changed": True,
                            "changed_sections": ["nutrition"],
                            "message_for_ai": "Plano atualizado com sucesso.",
                        }
                    ),
                }
            ]
        )

        self.assertTrue(summary["material_plan_change"])
        self.assertEqual(summary["tool_results"][0]["changed_sections"], ["nutrition"])

    def test_detect_explicit_plan_approval_for_active_plan_update(self):
        approval = AITrainerBrain.detect_explicit_plan_execution(
            user_input="pode atualizar",
            recent_history=[
                AIMessage(
                    content=(
                        "Posso atualizar o plano com novas calorias e macros. "
                        "Se estiver de acordo, me da o sinal verde."
                    )
                )
            ],
            plan_snapshot=PlanPromptContext(
                status="ACTIVE_PLAN",
                active_plan={"title": "Plano Atual"},
            ),
        )

        self.assertIsNotNone(approval)
        self.assertEqual(approval["mode"], "update_active_plan")
        self.assertEqual(approval["required_tool"], "update_plan_section")

    def test_detect_explicit_plan_approval_ignores_ambiguous_ok_without_plan_change_context(self):
        approval = AITrainerBrain.detect_explicit_plan_execution(
            user_input="ok",
            recent_history=[
                AIMessage(
                    content="Seu peso oscilou um pouco nesta semana, mas a tendencia ainda esta boa."
                )
            ],
            plan_snapshot=PlanPromptContext(
                status="ACTIVE_PLAN",
                active_plan={"title": "Plano Atual"},
            ),
        )

        self.assertIsNone(approval)

    def test_build_final_response_prompt_forbids_reconfirmation_on_explicit_approval(self):
        prompt = self.brain.build_final_response_prompt()
        system_prompt = prompt.messages[0].prompt.template

        self.assertIn("EXPLICIT_PLAN_APPROVAL=true", system_prompt)
        self.assertIn("Nao faca nova pergunta de confirmacao", system_prompt)

    async def test_send_message_ai_explicit_plan_approval_requires_update_attempt(self):
        captured = []
        approval_memory = MagicMock()
        approval_memory.load_memory_variables = MagicMock(
            return_value={
                "chat_history": [
                    AIMessage(
                        content=(
                            "Posso atualizar o plano com novas calorias e macros. "
                            "Se estiver de acordo, me da o sinal verde."
                        )
                    )
                ]
            }
        )
        self.mock_db.get_window_memory.return_value = approval_memory
        self.brain.prompt_builder.build_input_data = MagicMock(
            side_effect=lambda **kwargs: PromptBuilder.build_input_data(**kwargs)
        )

        async def _stream_with_tools(**kwargs):
            captured.append(kwargs)
            yield "Me confirma e eu aplico."
            yield {"type": "tools_summary", "tools_called": []}

        self.mock_llm.stream_with_tools = _stream_with_tools

        with patch(
            "src.services.trainer.build_plan_prompt_snapshot",
            return_value=PlanPromptContext(
                status="ACTIVE_PLAN",
                active_plan={"title": "Plano Atual"},
            ),
        ):
            chunks = []
            async for chunk in self.brain.send_message_ai(
                "test@test.com",
                "pode atualizar",
            ):
                chunks.append(chunk)

        payload = "".join(chunks)
        runtime_context = json.loads(captured[0]["input_data"]["runtime_context_json"])

        self.assertEqual(len(captured), 1)
        self.assertTrue(runtime_context["plan_execution"]["explicit_user_approval"])
        self.assertEqual(runtime_context["plan_execution"]["mode"], "update_active_plan")
        self.assertEqual(
            runtime_context["plan_execution"]["required_tool"],
            "update_plan_section",
        )
        self.assertIn("update_plan_section", payload)
        self.assertNotIn("me confirma", payload.lower())
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    async def test_send_message_ai_explicit_plan_approval_requires_create_attempt_when_discovery_complete(self):
        captured = []
        self.mock_db.get_plan.return_value = None
        self.mock_db.get_plan_discovery.return_value = MagicMock()
        approval_memory = MagicMock()
        approval_memory.load_memory_variables = MagicMock(
            return_value={
                "chat_history": [
                    AIMessage(
                        content=(
                            "Ja tenho tudo para criar o plano. "
                            "Se voce quiser, pode aplicar."
                        )
                    )
                ]
            }
        )
        self.mock_db.get_window_memory.return_value = approval_memory
        self.brain.prompt_builder.build_input_data = MagicMock(
            side_effect=lambda **kwargs: PromptBuilder.build_input_data(**kwargs)
        )

        async def _stream_with_tools(**kwargs):
            captured.append(kwargs)
            yield "Posso criar quando voce confirmar."
            yield {"type": "tools_summary", "tools_called": []}

        self.mock_llm.stream_with_tools = _stream_with_tools

        with patch(
            "src.services.trainer.build_plan_prompt_snapshot",
            return_value=PlanPromptContext(
                status="DISCOVERY_IN_PROGRESS",
                discovery={"missing_fields": [], "collected_fields": ["goal", "timeline"]},
            ),
        ):
            chunks = []
            async for chunk in self.brain.send_message_ai(
                "test@test.com",
                "manda ver",
            ):
                chunks.append(chunk)

        payload = "".join(chunks)
        runtime_context = json.loads(captured[0]["input_data"]["runtime_context_json"])

        self.assertEqual(len(captured), 1)
        self.assertTrue(runtime_context["plan_execution"]["explicit_user_approval"])
        self.assertEqual(runtime_context["plan_execution"]["mode"], "create_from_discovery")
        self.assertEqual(
            runtime_context["plan_execution"]["required_tool"],
            "create_plan_from_discovery",
        )
        self.assertIn("create_plan_from_discovery", payload)
        self.assertNotIn("confirmar", payload.lower())
        self.brain._executor.shutdown(wait=True, cancel_futures=True)

    def test_render_explicit_plan_execution_response_reports_validation_blocker(self):
        response = AITrainerBrain.render_explicit_plan_execution_response(
            approval_context={
                "mode": "update_active_plan",
                "required_tool": "update_plan_section",
            },
            tool_events=[
                {
                    "tool_name": "update_plan_section",
                    "content": json.dumps(
                        {
                            "status": "validation_error",
                            "saved": False,
                            "plan_materially_changed": False,
                            "message_for_ai": "A secao do plano nao foi atualizada por erro de validacao.",
                            "validation_errors": [{"msg": "target_date invalida"}],
                        }
                    ),
                }
            ],
            user_locale="pt-BR",
        )

        self.assertIn("target_date invalida", response)
        self.assertNotIn("confirma", response.lower())

    def test_add_to_mongo_history_persists_pair_in_one_batch(self):
        """Conversation persistence delegates the pair to one repository operation."""
        self.brain.add_to_mongo_history(
            "test@test.com",
            "Pode atualizar o plano",
            "Plano atualizado",
            {"trainer_type": "atlas"},
        )

        self.mock_db.add_many_to_history.assert_called_once()
        messages, session_id, trainer_type = (
            self.mock_db.add_many_to_history.call_args.args
        )
        self.assertEqual(session_id, "test@test.com")
        self.assertEqual(trainer_type, "atlas")
        self.assertEqual([message.sender for message in messages], [Sender.STUDENT, Sender.TRAINER])
        self.mock_db.add_to_history.assert_not_called()


if __name__ == "__main__":
    unittest.main()
