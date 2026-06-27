"""Tests for the Pydantic AI chat runner facade."""

from types import SimpleNamespace

import pytest

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.services.ai_chat.models import (
    CoachTurnOutput,
    OperationStatus,
    ToolAuditEntry,
    ToolResult,
)
from src.services.ai_chat.runner import ChatTurnRunner


class FakeAgent:
    def __init__(self, output: CoachTurnOutput | None = None):
        self.calls = 0
        self.output = output or CoachTurnOutput(
            public_message="Resposta final",
            operation_status=OperationStatus.NO_ACTION,
        )

    async def run(self, user_prompt, **kwargs):
        self.calls += 1
        self.user_prompt = user_prompt
        self.kwargs = kwargs
        return SimpleNamespace(output=self.output, usage=None, all_messages=lambda: [])


class FakeDatabase:
    def __init__(self):
        self.saved_messages = []
        self.logged_prompts = []
        self.history = []
        self.plan = None
        self.discovery = None

    def get_user_profile(self, email):
        return UserProfile(
            email=email,
            gender="Masculino",
            age=30,
            weight=80,
            height=175,
            goal="ganhar massa",
            goal_type="gain",
            weekly_rate=0.5,
        )

    def get_trainer_profile(self, email):
        profile = TrainerProfile(user_email=email, trainer_type="atlas")
        profile.preferred_language = "pt-BR"
        return profile

    def get_plan(self, _email):
        return self.plan

    def get_plan_discovery(self, _email):
        return self.discovery

    def get_chat_history(self, *_args, **_kwargs):
        return self.history

    def add_many_to_history(self, messages, session_id, trainer_type=None):
        self.saved_messages.append((messages, session_id, trainer_type))

    def increment_user_message_counts(self, *_args, **_kwargs):
        return None

    def log_prompt(self, user_email, prompt_data):
        self.logged_prompts.append((user_email, prompt_data))


@pytest.mark.asyncio
async def test_runner_calls_agent_once_and_persists_public_pair():
    agent = FakeAgent()
    database = FakeDatabase()
    runner = ChatTurnRunner(database=database, qdrant_client=None, agent=agent)

    chunks = [
        chunk
        async for chunk in runner.stream_turn(
            user_email="test@test.com",
            user_input="oi",
            background_tasks=None,
            message_options=None,
        )
    ]

    payload = "".join(chunks)
    assert agent.calls == 1
    assert "toolsets" in agent.kwargs
    assert agent.kwargs["toolsets"]
    assert agent.kwargs["model_settings"]["extra_body"]["user"].startswith("fityq:")
    assert "test@test.com" not in agent.kwargs["model_settings"]["extra_body"]["user"]
    assert '"stage":"preparing_context"' in payload
    assert '"stage":"using_tools"' in payload
    assert '"stage":"writing_reply"' in payload
    assert '"text":"Resposta final"' in payload
    assert database.saved_messages
    saved_pair = database.saved_messages[0][0]
    assert [message.sender for message in saved_pair] == [Sender.STUDENT, Sender.TRAINER]
    logged = database.logged_prompts[0][1]
    assert logged["available_tools_count"] <= 10
    assert "plan_ops" in logged["available_tool_names"]
    assert "hevy_ops" not in logged["available_tool_names"]


@pytest.mark.asyncio
async def test_runner_injects_required_tool_after_explicit_plan_update_approval():
    agent = FakeAgent()
    database = FakeDatabase()
    database.plan = object()
    database.history = [
        ChatHistory(
            text="Posso atualizar seu plano para reduzir o volume de pernas.",
            sender=Sender.TRAINER,
            timestamp="2026-06-27T10:00:00",
        )
    ]
    runner = ChatTurnRunner(database=database, qdrant_client=None, agent=agent)

    chunks = [
        chunk
        async for chunk in runner.stream_turn(
            user_email="test@test.com",
            user_input="ok, pode aplicar",
            background_tasks=None,
            message_options=None,
        )
    ]

    payload = "".join(chunks)
    assert agent.calls == 1
    assert '"stage":"using_tools"' in payload
    assert "plan_execution" in agent.user_prompt
    assert '"explicit_user_approval": true' in agent.user_prompt
    assert '"required_tool": "update_plan_section"' in agent.user_prompt
    tool_names = {
        name
        for toolset in agent.kwargs["toolsets"]
        for name in toolset.tools
    }
    assert "plan_ops" in tool_names
    assert '"text":"Nao executei a mudanca solicitada.' in payload


class FakeAgentWithAuditedPayload(FakeAgent):
    async def run(self, user_prompt, **kwargs):
        deps = kwargs["deps"]
        deps.tool_audit.append(
            ToolAuditEntry(
                tool_name="get_workouts_raw",
                args_preview={"limit": 200},
                result=ToolResult(
                    tool_name="get_workouts_raw",
                    status="success",
                    message_for_ai="Dados carregados.",
                    payload={
                        "items": [
                            {
                                "notes": "x" * 1000,
                                "authorization": "secret-token",
                            }
                        ],
                        "total": 1,
                    },
                ),
            )
        )
        return await super().run(user_prompt, **kwargs)


@pytest.mark.asyncio
async def test_runner_logs_tool_result_preview_without_raw_payload():
    agent = FakeAgentWithAuditedPayload()
    database = FakeDatabase()
    runner = ChatTurnRunner(database=database, qdrant_client=None, agent=agent)

    [
        chunk
        async for chunk in runner.stream_turn(
            user_email="test@test.com",
            user_input="analise meus dados brutos",
            background_tasks=None,
            message_options=None,
        )
    ]

    logged = database.logged_prompts[0][1]
    audit_entry = logged["tool_audit"][0]
    assert audit_entry["tool_name"] == "get_workouts_raw"
    assert audit_entry["result"]["status"] == "success"
    assert audit_entry["result"]["payload_preview"] == "dict(keys=['items', 'total'])"
    assert "payload" not in audit_entry["result"]
    assert "secret-token" not in str(logged)
    assert "x" * 100 not in str(logged)


def test_runner_logs_openrouter_cache_usage_tokens():
    database = FakeDatabase()
    runner = ChatTurnRunner(database=database, qdrant_client=None, agent=FakeAgent())
    result = SimpleNamespace(
        usage=SimpleNamespace(
            input_tokens=120,
            output_tokens=30,
            requests=1,
            cache_read_tokens=80,
            cache_write_tokens=40,
        )
    )

    runner._log_run(  # pylint: disable=protected-access
        user_email="test@test.com",
        status="success",
        error_type=None,
        start=0,
        context_ms=1,
        agent_ms=2,
        message_chars=10,
        deps=None,
        result=result,
        history_messages_count=3,
        selected_toolsets=[],
    )

    logged = database.logged_prompts[0][1]
    assert logged["cache_read_tokens"] == 80
    assert logged["cache_write_tokens"] == 40
