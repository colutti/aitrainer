"""One-turn Pydantic AI chat runner."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import AsyncIterator, Any

from fastapi import BackgroundTasks

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.core.config import settings
from src.core.logs import logger
from src.services.ai_chat.agent import build_chat_agent
from src.services.ai_chat.context import build_runtime_context
from src.services.ai_chat.deps import ChatAgentDeps
from src.services.ai_chat.models import ChatRunLog, CoachTurnOutput, ToolResult
from src.services.ai_chat.plan_execution import detect_plan_execution_requirement
from src.services.ai_chat.prompts import build_user_prompt
from src.services.ai_chat.sse import format_sse_event
from src.services.ai_chat.tools.base import audit_entry_preview_for_log
from src.services.ai_chat.tools.registry import select_chat_toolsets, selected_toolset_summary
from src.services.ai_chat.validation import validate_turn_output
from src.services.hevy_service import HevyService


class ChatTurnRunner:  # pylint: disable=too-few-public-methods
    """Run one user message through a single Pydantic AI agent run."""

    def __init__(self, database, qdrant_client=None, agent: Any | None = None):
        self.database = database
        self.qdrant_client = qdrant_client
        self.agent = agent or build_chat_agent()
        self.hevy_service = None
        if hasattr(database, "workouts_repo"):
            try:
                self.hevy_service = HevyService(workout_repository=database.workouts_repo)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Hevy service unavailable for chat tools: %s", exc)

    async def stream_turn(
        # pylint: disable=too-many-locals
        self,
        *,
        user_email: str,
        user_input: str,
        background_tasks: BackgroundTasks | None,
        message_options: dict | None,
    ) -> AsyncIterator[str]:
        """Stream one user turn as structured SSE frames."""
        start = time.perf_counter()
        context_ms = 0
        agent_ms = 0
        profile = None
        trainer_profile = None
        deps = None
        selected_toolsets = []
        try:
            yield format_sse_event("status", {"stage": "preparing_context"})
            context_start = time.perf_counter()
            profile = self.database.get_user_profile(user_email)
            if profile is None:
                raise ValueError("User profile not found")
            trainer_profile = self.database.get_trainer_profile(user_email)
            if trainer_profile is None:
                trainer_profile = TrainerProfile(user_email=user_email, trainer_type="atlas")
                self.database.save_trainer_profile(trainer_profile)

            runtime_context = build_runtime_context(
                database=self.database,
                user_email=user_email,
                profile=profile,
                trainer_profile=trainer_profile,
                is_telegram=bool((message_options or {}).get("is_telegram")),
            )
            public_history = []
            if hasattr(self.database, "get_chat_history"):
                public_history = self.database.get_chat_history(
                    user_email, limit=settings.MAX_SHORT_TERM_MEMORY_MESSAGES, offset=0
                )
            plan_execution = detect_plan_execution_requirement(
                user_input=user_input,
                recent_history=public_history,
                runtime_context=runtime_context,
            )
            if plan_execution:
                runtime_context["plan_execution"] = plan_execution
            deps = ChatAgentDeps(
                user_email=user_email,
                database=self.database,
                qdrant_client=self.qdrant_client,
                profile=profile,
                trainer_profile=trainer_profile,
                runtime_context=runtime_context,
                hevy_service=self.hevy_service,
            )
            history = []
            if hasattr(self.database, "get_pydantic_ai_history"):
                history = self.database.get_pydantic_ai_history(
                    user_email, limit=settings.MAX_SHORT_TERM_MEMORY_MESSAGES
                )
            selected_toolsets = select_chat_toolsets(
                user_input=user_input,
                runtime_context=runtime_context,
            )
            context_ms = int((time.perf_counter() - context_start) * 1000)

            yield format_sse_event("status", {"stage": "using_tools"})
            agent_start = time.perf_counter()
            result = await asyncio.wait_for(
                self.agent.run(
                    build_user_prompt(user_input, runtime_context),
                    deps=deps,
                    message_history=history,
                    conversation_id=user_email,
                    metadata={"user_email": user_email},
                    toolsets=selected_toolsets,
                ),
                timeout=float(settings.LLM_STREAM_TIMEOUT_SECONDS),
            )
            agent_ms = int((time.perf_counter() - agent_start) * 1000)

            raw_output = result.output
            output = (
                raw_output
                if isinstance(raw_output, CoachTurnOutput)
                else CoachTurnOutput.model_validate(raw_output)
            )
            tool_results = [
                audit.result for audit in deps.tool_audit if isinstance(audit.result, ToolResult)
            ]
            validated = validate_turn_output(
                output=output,
                tool_results=tool_results,
                user_locale=getattr(trainer_profile, "preferred_language", None),
                required_tool=(
                    runtime_context.get("plan_execution", {}) or {}
                ).get("required_tool"),
            )

            yield format_sse_event("status", {"stage": "writing_reply"})
            yield format_sse_event("delta", {"text": validated.public_message})
            yield format_sse_event("status", {"stage": "saving"})

            self._persist_success(
                user_email=user_email,
                user_input=user_input,
                final_response=validated.public_message,
                trainer_type=getattr(trainer_profile, "trainer_type", "atlas") or "atlas",
                image_payloads=(message_options or {}).get("image_payloads"),
                background_tasks=background_tasks,
            )
            self._log_run(
                user_email=user_email,
                status="success",
                error_type=None,
                start=start,
                context_ms=context_ms,
                agent_ms=agent_ms,
                message_chars=len(user_input),
                deps=deps,
                result=result,
                history_messages_count=len(history),
                selected_toolsets=selected_toolsets,
            )
            yield format_sse_event(
                "done",
                {"text": validated.public_message, "persisted": True},
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.exception("Pydantic AI chat turn failed for %s", user_email)
            self._log_run(
                user_email=user_email,
                status="error",
                error_type=type(exc).__name__,
                start=start,
                context_ms=context_ms,
                agent_ms=agent_ms,
                message_chars=len(user_input),
                deps=deps,
                result=None,
                history_messages_count=0,
                selected_toolsets=selected_toolsets,
            )
            yield format_sse_event(
                "error",
                {"message": "Desculpe, ocorreu um erro interno. Tente novamente em instantes."},
            )

    def _persist_success(
        # pylint: disable=too-many-arguments
        self,
        *,
        user_email: str,
        user_input: str,
        final_response: str,
        trainer_type: str,
        image_payloads: list[dict[str, str]] | None,
        background_tasks: BackgroundTasks | None,
    ) -> None:
        def persist() -> None:
            now = datetime.now().isoformat()
            user_message = ChatHistory(
                sender=Sender.STUDENT,
                text=user_input,
                timestamp=now,
                images=image_payloads,
            )
            ai_message = ChatHistory(
                sender=Sender.TRAINER,
                text=final_response,
                timestamp=now,
                trainer_type=trainer_type,
            )
            self.database.add_many_to_history(
                [user_message, ai_message], user_email, trainer_type
            )
            self.database.increment_user_message_counts(user_email)

        if background_tasks:
            background_tasks.add_task(persist)
        else:
            persist()

    def _log_run(
        # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        user_email: str,
        status: str,
        error_type: str | None,
        start: float,
        context_ms: int,
        agent_ms: int,
        message_chars: int,
        deps: ChatAgentDeps | None,
        result: Any | None,
        history_messages_count: int,
        selected_toolsets: list,
    ) -> None:
        usage = getattr(result, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0) if usage else 0
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0) if usage else 0
        requests = int(getattr(usage, "requests", 0) or 0) if usage else 0
        audit = deps.tool_audit if deps is not None else []
        audit_for_log = [audit_entry_preview_for_log(entry) for entry in audit]
        toolset_ids, available_tool_names = selected_toolset_summary(selected_toolsets)
        log = ChatRunLog(
            status=status,
            error_type=error_type,
            requested_model=settings.OPENROUTER_CHAT_MODEL,
            service_tier=settings.OPENROUTER_SERVICE_TIER,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            duration_ms=int((time.perf_counter() - start) * 1000),
            context_load_ms=context_ms,
            agent_run_ms=agent_ms,
            internal_requests=requests,
            tool_calls_count=len(audit),
            selected_toolsets=toolset_ids,
            available_tool_names=available_tool_names,
            available_tools_count=len(available_tool_names),
            tools_called=[entry.tool_name for entry in audit],
            tool_audit=audit_for_log,
            message_chars=message_chars,
            history_messages_count=history_messages_count,
        )
        try:
            self.database.log_prompt(user_email, log.model_dump())
        except Exception as log_exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to log Pydantic AI run: %s", log_exc)
