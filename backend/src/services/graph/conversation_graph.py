"""Conversation graph runtime."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import uuid4
from typing import Any, Optional

from langchain_core.prompts import ChatPromptTemplate

from src.core.langsmith import create_graph_run_context, create_node_run_context
from src.core.logs import logger
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.agents.config_registry import AgentConfigRegistry
from src.services.agents.node_tool_policy import get_node_llm_tools
from src.services.graph.conversation_contract import (
    ActionStatus,
    build_conversation_summary,
    build_snapshot,
    default_conversation_state,
    parse_latest_summary,
    parse_latest_snapshot,
    resolve_pending_action,
)
from src.services.plan_service import build_plan_prompt_snapshot
from src.repositories.event_repository import EventRepository



_INJECTION_PATTERNS = [
    r"ignore previous instructions",
    r"show me .*prompt",
    r"reveal .*system",
    r"developer message",
    r"prompt injection",
    r"print your instructions",
    r"show internal",
]
_EVENT_ID_PATTERN = re.compile(r"([a-f0-9]{24}|[a-f0-9-]{8,})", re.IGNORECASE)
_ISO_DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_MEMORY_ID_PATTERN = re.compile(r"\bID:\s*([a-f0-9-]{8,})\b", re.IGNORECASE)
_EVENT_LINE_PATTERN = re.compile(
    r"- \*\*(?P<title>.+?)\*\* \((?P<id>[a-f0-9-]{8,})\)\n\s+📅 (?P<date>[^\n|]+)",
    re.IGNORECASE,
)


@dataclass
class GraphState:
    """Shared graph state."""

    user_email: str
    user_input_raw: str
    channel: str
    request_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str = ""
    turn_id: str = field(default_factory=lambda: str(uuid4()))
    is_telegram: bool = False
    user_images: Optional[list[dict[str, str]]] = None
    security_status: str = "safe"
    user_input_sanitized: str = ""
    shared_context: dict[str, Any] = field(default_factory=dict)
    coach_response: str = ""
    final_response: str = ""
    tools_called: list[str] = field(default_factory=list)
    persistence_actions: list[str] = field(default_factory=list)
    blocked_segments: list[str] = field(default_factory=list)
    node_outputs: dict[str, str] = field(default_factory=dict)
    node_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    plan_needs_revision: bool = False
    persistence_intents: dict[str, Any] = field(default_factory=dict)
    conversation_state: dict[str, Any] = field(default_factory=default_conversation_state)
    specialist_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    specialist_pending_actions: dict[str, dict[str, Any]] = field(default_factory=dict)
    request: dict[str, Any] = field(default_factory=dict)
    security: dict[str, Any] = field(default_factory=dict)
    routing: dict[str, Any] = field(default_factory=dict)
    response: dict[str, Any] = field(default_factory=dict)
    ops: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.request = {
            "raw_input": self.user_input_raw,
            "sanitized_input": self.user_input_sanitized,
            "channel": self.channel,
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "user_images": self.user_images or [],
        }
        self.security = {
            "status": self.security_status,
            "blocked_segments": self.blocked_segments,
        }
        self.routing = {
            "intent": "general",
        }
        self.response = {
            "technical": self.coach_response,
            "final": self.final_response,
        }
        self.ops = {
            "tools_called": self.tools_called,
            "node_outcomes": self.node_metadata,
            "node_outputs": self.node_outputs,
        }


class ConversationGraphRunner:
    """Orchestrates conversation through explicit nodes."""

    NODE_ORDER = (
        "session_context",
        "prompt_security",
        "training_specialist",
        "nutrition_specialist",
        "plan_specialist",
        "coach_reply",
        "memory_hub",
    )

    def __init__(self, brain, registry: AgentConfigRegistry):
        self._brain = brain
        self._registry = registry

    @staticmethod
    def _escape_template_text(text: str) -> str:
        return text.replace("{", "{{").replace("}", "}}")

    @staticmethod
    def _parse_iso_date(value: str | None) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value).strip())
        except ValueError:
            return None

    @classmethod
    def _infer_event_recurrence(cls, value: str | None) -> str:
        if not value:
            return "none"
        normalized = cls._normalize_text(value)
        if any(token in normalized for token in ("semanal", "semana", "segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo")):
            return "weekly"
        if any(token in normalized for token in ("mensal", "mes", "mês")):
            return "monthly"
        return "none"

    @classmethod
    def _normalize_event_date(cls, value: str | None) -> str:
        if not value:
            return ""
        normalized = str(value).strip()
        if cls._parse_iso_date(normalized):
            return normalized
        match = _ISO_DATE_PATTERN.search(normalized)
        return match.group(1) if match else ""

    @classmethod
    def _build_plan_lifecycle_flags(
        cls,
        *,
        plan_window_end: str | None,
        next_review: str | None,
        current_date: str | None,
    ) -> dict[str, bool]:
        today = cls._parse_iso_date(current_date)
        target = cls._parse_iso_date(plan_window_end)
        review = cls._parse_iso_date(next_review)
        if today is None:
            return {"timeline_expired": False, "next_review_due": False}
        return {
            "timeline_expired": bool(target and target <= today),
            "next_review_due": bool(review and review <= today),
        }

    @staticmethod
    def _infer_response_locale(text: str) -> str:
        normalized = ConversationGraphRunner._normalize_text(text)
        spanish_markers = {
            "grasa",
            "carbos",
            "carbohidratos",
            "entrené",
            "entrene",
            "hoy",
            "mañana",
            "manana",
            "lunes",
            "martes",
            "miércoles",
            "miercoles",
            "jueves",
            "viernes",
            "sábado",
            "sabado",
            "domingo",
            "peso",
            "proteína",
            "proteina",
        }
        english_markers = {
            "today",
            "trained",
            "training",
            "protein",
            "carbs",
            "calories",
            "back",
            "today",
            "want",
            "maintain",
            "muscle",
            "weight",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        }
        spanish_hits = sum(1 for marker in spanish_markers if marker in normalized)
        english_hits = sum(1 for marker in english_markers if marker in normalized)
        if spanish_hits > english_hits:
            return "es-ES"
        if english_hits > spanish_hits:
            return "en-US"
        return "pt-BR"

    @staticmethod
    def _resolve_user_locale(preferred_language: str | None, text: str) -> str:
        normalized_preference = str(preferred_language or "").strip()
        if normalized_preference in {"pt-BR", "en-US", "es-ES"}:
            return normalized_preference
        return ConversationGraphRunner._infer_response_locale(text)

    async def run_stream(
        self,
        *,
        user_email: str,
        user_input: str,
        is_telegram: bool,
        user_images: Optional[list[dict[str, str]]],
        background_tasks,
        turn_id: str | None = None,
    ):
        """Run graph and yield streamed text."""
        started_at = datetime.utcnow()
        state = GraphState(
            user_email=user_email,
            user_input_raw=user_input,
            channel="telegram" if is_telegram else "app",
            conversation_id=user_email,
            is_telegram=is_telegram,
            user_images=user_images,
            user_input_sanitized=user_input,
            turn_id=turn_id or str(uuid4()),
        )
        state.request["sanitized_input"] = user_input

        trace_metadata = {
            "request_id": state.request_id,
            "conversation_id": state.conversation_id,
            "turn_id": state.turn_id,
            "channel": state.channel,
            "graph_nodes": list(self.NODE_ORDER),
            "node_configs": self._registry.as_metadata(),
        }
        graph_error: str | None = None
        try:
            with create_graph_run_context(
                run_name="graph.conversation",
                metadata=trace_metadata,
            ):
                for node_name in self.NODE_ORDER:
                    yield {"type": "status", "node": node_name}
                    await self._run_node(node_name, state)
                    if node_name == "prompt_security" and state.security_status != "safe":
                        break
                    if node_name == "plan_specialist" and state.security_status == "safe":
                        self._resolve_pending_actions(state)

                if state.security_status != "safe":
                    state.coach_response = self._blocked_response()
                    state.final_response = state.coach_response
                    state.response["technical"] = state.coach_response
                    state.response["final"] = state.final_response

                snapshot = build_snapshot(state.conversation_state)
                self._brain.add_system_message_to_history(state.user_email, snapshot)
                logger.info(
                    "graph.turn_completed request_id=%s conversation_id=%s turn_id=%s domain=%s security=%s tools_called=%s persistence_actions=%s",
                    state.request_id,
                    state.conversation_id,
                    state.turn_id,
                    state.conversation_state.get("active_domain", "general"),
                    state.security_status,
                    state.tools_called,
                    state.persistence_actions,
                )

                yield {"type": "response", "text": state.final_response}

                await self._brain.finalize_ai_response(
                    user_email=user_email,
                    user_input=user_input,
                    final_response=state.final_response,
                    metadata={
                        "trainer_type": state.shared_context.get("trainer_type", "atlas"),
                        "needs_cycle_reset": bool(state.shared_context.get("needs_cycle_reset", False)),
                        "background_tasks": background_tasks,
                        "log_callback": self._brain.get_log_callback(background_tasks),
                        "user_images": user_images,
                    },
                )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            graph_error = str(exc)
            raise
        finally:
            if self._brain.is_graph_debug_enabled():
                self._brain.store_graph_debug_trace(
                    state.turn_id,
                    self._build_debug_trace(
                        state=state,
                        started_at=started_at,
                        ended_at=datetime.utcnow(),
                        graph_error=graph_error,
                    ),
                )

    def _resolve_pending_actions(self, state: GraphState) -> None:
        """Merge specialist pending_action suggestions using priority."""
        merged = resolve_pending_action(state.specialist_pending_actions)
        last_action = ActionStatus.NO_ACTION_NEEDED.value
        for node_name in ("training_specialist", "nutrition_specialist", "plan_specialist"):
            spec = state.specialist_states.get(node_name, {})
            status = spec.get("action_status", "")
            if status and status != ActionStatus.NO_ACTION_NEEDED.value:
                last_action = status
                break
        state.conversation_state["pending_action"] = merged
        state.conversation_state["last_action_status"] = last_action
        active_domain = self._derive_active_domain(state)
        state.conversation_state["active_domain"] = active_domain
        state.routing["intent"] = active_domain

    @staticmethod
    def _derive_active_domain(state: GraphState) -> str:
        """Derive active_domain from specialist states for telemetry."""
        kind = state.conversation_state.get("pending_action", {}).get("kind", "none")
        if kind in ("plan_discovery", "plan_review"):
            return "plan"
        plan_status = state.specialist_states.get("plan_specialist", {}).get("action_status", "")
        if plan_status and plan_status != ActionStatus.NO_ACTION_NEEDED.value:
            return "plan"
        training_status = state.specialist_states.get("training_specialist", {}).get("action_status", "")
        nutrition_status = state.specialist_states.get("nutrition_specialist", {}).get("action_status", "")
        training_active = bool(training_status and training_status != ActionStatus.NO_ACTION_NEEDED.value)
        nutrition_active = bool(nutrition_status and nutrition_status != ActionStatus.NO_ACTION_NEEDED.value)
        if training_active and nutrition_active:
            return "multi_domain"
        if training_active:
            return "training"
        if nutrition_active:
            return "nutrition"
        return "general"

    async def _run_node(self, node_name: str, state: GraphState) -> None:
        cfg = self._registry.get_node_config(node_name)
        base_meta = {
            "config_hash": cfg.config_hash,
            "config_version": cfg.version,
            "model": cfg.model_name,
            "request_id": state.request_id,
            "conversation_id": state.conversation_id,
            "turn_id": state.turn_id,
        }
        node_started_at = datetime.utcnow()
        state.node_metadata[node_name] = {
            **base_meta,
            "started_at": node_started_at.isoformat(),
        }
        if not cfg.enabled:
            state.node_metadata[node_name]["status"] = "skipped_disabled"
            node_completed_at = datetime.utcnow()
            state.node_metadata[node_name]["completed_at"] = node_completed_at.isoformat()
            state.node_metadata[node_name]["duration_ms"] = int(
                (node_completed_at - node_started_at).total_seconds() * 1000
            )
            logger.info(
                "graph.node_skipped node=%s cfg=%s request_id=%s",
                node_name,
                cfg.config_hash,
                state.request_id,
            )
            return
        logger.info(
            "graph.node_started node=%s cfg=%s request_id=%s",
            node_name,
            cfg.config_hash,
            state.request_id,
        )
        node = getattr(self, f"_node_{node_name}")
        try:
            with create_node_run_context(node_name=node_name, metadata=base_meta):
                if asyncio.iscoroutinefunction(node):
                    await node(state)
                else:
                    node(state)
            state.node_metadata[node_name]["status"] = "completed"
            state.node_metadata[node_name]["output_preview"] = self._truncate(
                state.node_outputs.get(node_name, ""),
                320,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            state.node_metadata[node_name]["status"] = "failed"
            state.node_metadata[node_name]["error"] = str(exc)
            raise
        finally:
            node_completed_at = datetime.utcnow()
            state.node_metadata[node_name]["completed_at"] = node_completed_at.isoformat()
            state.node_metadata[node_name]["duration_ms"] = int(
                (node_completed_at - node_started_at).total_seconds() * 1000
            )
        logger.info(
            "graph.node_completed node=%s request_id=%s",
            node_name,
            state.request_id,
        )

    def _build_debug_trace(
        self,
        *,
        state: GraphState,
        started_at: datetime,
        ended_at: datetime,
        graph_error: str | None,
    ) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for node_name in self.NODE_ORDER:
            meta = dict(state.node_metadata.get(node_name, {}))
            nodes.append(
                {
                    "node_name": node_name,
                    "status": meta.get("status", "pending"),
                    "started_at": meta.get("started_at"),
                    "completed_at": meta.get("completed_at"),
                    "duration_ms": meta.get("duration_ms"),
                    "output_preview": meta.get("output_preview", ""),
                    "error": meta.get("error"),
                    "config_hash": meta.get("config_hash"),
                    "config_version": meta.get("config_version"),
                    "model": meta.get("model"),
                    "tools_called": meta.get("tools_called", []),
                }
            )
        return {
            "user_email": state.user_email,
            "request_id": state.request_id,
            "conversation_id": state.conversation_id,
            "turn_id": state.turn_id,
            "channel": state.channel,
            "status": "error" if graph_error else "success",
            "error": graph_error,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "duration_ms": int((ended_at - started_at).total_seconds() * 1000),
            "intent": state.conversation_state.get("active_domain", "general"),
            "security_status": state.security_status,
            "plan_needs_revision": state.plan_needs_revision,
            "tools_called": state.tools_called,
            "persistence_actions": state.persistence_actions,
            "final_response": state.final_response,
            "technical_response": state.coach_response,
            "node_outputs": state.node_outputs,
            "nodes": nodes,
        }

    async def _node_session_context(self, state: GraphState) -> None:
        profile = self._brain.get_or_create_user_profile(state.user_email)
        trainer_profile = self._brain.get_or_create_trainer_profile(state.user_email, profile)
        needs_cycle_reset = self._brain.check_message_limits(profile)

        metabolism = await asyncio.to_thread(
            AdaptiveTDEEService(self._brain.database).calculate_tdee,
            state.user_email,
        )
        plan = await asyncio.to_thread(self._brain.database.get_plan, state.user_email)
        events = await asyncio.to_thread(
            EventRepository(self._brain.database.database).get_active_events,
            state.user_email,
        )
        history_payload = (
            await asyncio.to_thread(
                self._brain.database.get_window_memory(
                    session_id=state.user_email, k=12
                ).load_memory_variables,
                {},
            )
        ).get("chat_history", [])
        raw_system_msgs = [
            str(msg.content)
            for msg in history_payload
            if getattr(msg, "type", None) == "system"
        ]
        previous_state = parse_latest_snapshot(raw_system_msgs)
        if previous_state:
            state.conversation_state = previous_state
        conversation_summary = parse_latest_summary(raw_system_msgs)
        input_data = self._brain.prompt_builder.build_input_data(
            profile=profile,
            trainer_profile_summary=trainer_profile.get_trainer_profile_summary(),
            user_profile_summary=profile.get_profile_summary(),
            formatted_history_msgs=self._brain.format_history_as_messages(history_payload),
            user_input=state.user_input_sanitized,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            agenda_events=events,
            plan_snapshot=build_plan_prompt_snapshot(plan) if plan else None,
            metabolism_data=metabolism,
        )
        detected_locale = self._resolve_user_locale(
            trainer_profile.preferred_language,
            state.user_input_sanitized or state.user_input_raw,
        )
        input_data["user_locale"] = detected_locale
        runtime_context = dict(input_data.get("runtime_context") or {})
        session_ctx = dict(runtime_context.get("session") or {})
        session_ctx["channel"] = state.channel
        session_ctx["response_locale"] = detected_locale
        runtime_context["session"] = session_ctx
        input_data["runtime_context"] = runtime_context
        plan_lifecycle = self._build_plan_lifecycle_flags(
            plan_window_end=(
                plan.timeline.target_date.strftime("%Y-%m-%d") if plan else None
            ),
            next_review=(
                str(plan.current_summary.next_review).strip()
                if plan and plan.current_summary.next_review
                else None
            ),
            current_date=input_data.get("current_date"),
        )
        runtime_plan = dict(runtime_context.get("plan") or {})
        runtime_plan["lifecycle"] = plan_lifecycle
        runtime_context["plan"] = runtime_plan
        input_data["runtime_context"] = runtime_context
        input_data["runtime_context_json"] = json.dumps(
            runtime_context, ensure_ascii=True, sort_keys=True
        )
        state.shared_context = {
            "profile": profile,
            "trainer_profile_obj": trainer_profile,
            "input_data": input_data,
            "trainer_type": trainer_profile.trainer_type,
            "needs_cycle_reset": needs_cycle_reset,
            "request_id": state.request_id,
            "conversation_id": state.conversation_id,
            "turn_id": state.turn_id,
        }
        state.shared_context["user_profile_summary"] = input_data.get("user_profile", "")
        state.shared_context["trainer_identity"] = (
            f"trainer_type={trainer_profile.trainer_type}; "
            f"preferred_language={trainer_profile.preferred_language or 'pt-BR'}; "
            f"personality_level={trainer_profile.personality_level or 'balanced'}"
        )
        state.shared_context["trainer_persona"] = input_data.get("trainer_profile", "")
        state.shared_context["agenda_section"] = input_data.get("agenda_section", "")
        state.shared_context["plan_section"] = input_data.get("plan_section", "")
        state.shared_context["metabolism_section"] = input_data.get("metabolism_section", "")
        raw_history = input_data.get("formatted_history", "")
        state.shared_context["history_summary"] = raw_history
        state.shared_context["conversation_summary"] = conversation_summary or ""
        if raw_history:
            try:
                cleaned = await self._run_llm_node(
                    node_name="session_context",
                    state=state,
                    allowed_tools=set(),
                )
                clean_len = len(cleaned)
                fallback_threshold = max(10, int(len(raw_history) * 0.2))
                if clean_len <= fallback_threshold:
                    logger.info(
                        "history_sanitize.fallback_too_short chars_in=%d chars_out=%d ratio=%.2f",
                        len(raw_history), clean_len,
                        clean_len / max(len(raw_history), 1),
                    )
                    cleaned = raw_history
                else:
                    logger.info(
                        "history_sanitize.completed chars_in=%d chars_out=%d",
                        len(raw_history), clean_len,
                    )
                if conversation_summary:
                    cleaned = f"[CONVERSATION_SUMMARY]\n{conversation_summary}\n\n[RECENT_MESSAGES]\n{cleaned}"
                state.shared_context["history_summary_neutral"] = cleaned
            except Exception:  # pylint: disable=broad-exception-caught
                logger.warning("history_sanitize.fallback_raw", exc_info=True)
                neutral = raw_history
                if conversation_summary:
                    neutral = f"[CONVERSATION_SUMMARY]\n{conversation_summary}\n\n[RECENT_MESSAGES]\n{raw_history}"
                state.shared_context["history_summary_neutral"] = neutral
        else:
            state.shared_context["history_summary_neutral"] = raw_history

        if conversation_summary and state.shared_context["history_summary"]:
            state.shared_context["history_summary"] = (
                f"[CONVERSATION_SUMMARY]\n{conversation_summary}\n\n"
                f"[RECENT_MESSAGES]\n{state.shared_context['history_summary']}"
            )
        state.shared_context["plan_lifecycle"] = plan_lifecycle
        state.shared_context["persistence_candidates"] = {"memory": [], "event": []}
        state.request["sanitized_input"] = state.user_input_sanitized
        state.node_outputs["session_context"] = "hydrated"

    async def _node_prompt_security(self, state: GraphState) -> None:
        lowered = state.user_input_raw.lower()
        for pattern in _INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                state.security_status = "blocked"
                state.user_input_sanitized = ""
                state.blocked_segments.append(pattern)
                state.node_outputs["prompt_security"] = f"blocked:{pattern}"
                logger.warning(
                    "graph.prompt_security_blocked request_id=%s turn_id=%s reason=%s",
                    state.request_id,
                    state.turn_id,
                    pattern,
                )
                return
        classifier = await self._run_llm_node(
            node_name="prompt_security",
            state=state,
            allowed_tools=set(),
            message_override=state.user_input_raw,
        )
        parsed = self._parse_json_object(classifier)
        status = str(parsed.get("status", "safe")).lower()
        if status not in {"safe", "blocked"}:
            status = "safe"
        state.security_status = status
        state.security["status"] = status
        sanitized = str(parsed.get("sanitized", state.user_input_raw)).strip()
        state.user_input_sanitized = sanitized if status == "safe" else ""
        state.request["sanitized_input"] = state.user_input_sanitized
        if status == "blocked":
            reason = str(parsed.get("reason", "security_policy"))
            state.blocked_segments.append(reason)
            state.security["blocked_segments"] = state.blocked_segments
            state.node_outputs["prompt_security"] = f"blocked:{reason}"
            logger.warning(
                "graph.prompt_security_blocked request_id=%s turn_id=%s reason=%s",
                state.request_id,
                state.turn_id,
                reason,
            )
            return
        state.security_status = "safe"
        if not state.user_input_sanitized:
            state.user_input_sanitized = state.user_input_raw
            state.request["sanitized_input"] = state.user_input_sanitized
        state.node_outputs["prompt_security"] = "safe"

    @staticmethod
    def _is_training_plan_context(state: GraphState) -> bool:
        conversation_state = state.conversation_state or {}
        active_domain = conversation_state.get("active_domain", "")
        if active_domain == "plan":
            return True
        pending_action = conversation_state.get("pending_action", {})
        if isinstance(pending_action, dict):
            kind = pending_action.get("kind", "")
            if kind in ("plan_discovery", "plan_review"):
                return True
        return False

    @staticmethod
    def _has_material_training_summary(text: str) -> bool:
        if not text or not text.strip():
            return False
        text_lower = text.lower()
        has_routine = "routine:" in text_lower or "rotina:" in text_lower
        has_progression = "progression" in text_lower or "progressão" in text_lower or "progressive" in text_lower
        has_effort = "rpe" in text_lower or "rir" in text_lower or "effort" in text_lower or "esforço" in text_lower
        has_sets_reps = "x" in text_lower and ("rep" in text_lower or "reps" in text_lower or "repetições" in text_lower)
        exercise_like_lines = [
            line for line in text.splitlines()
            if line.strip().startswith("-")
            and any(
                token in line.lower()
                for token in ["x", "rpe", "rir", "rest", "descanso"]
            )
        ]
        return (
            has_routine
            and has_progression
            and has_effort
            and has_sets_reps
            and len(exercise_like_lines) >= 4
        )

    async def _node_training_specialist(self, state: GraphState) -> None:
        peer_output = state.node_outputs.get("nutrition_specialist", "")
        peer_block = f"\n\nANALISE_NUTRICAO:\n{peer_output}" if peer_output else ""
        response = await self._run_llm_node(
            node_name="training_specialist",
            state=state,
            extra_context=f"{self._shared_context_payload(state)}{peer_block}",
            allowed_tools=get_node_llm_tools("training_specialist"),
        )
        parsed = self._parse_json_object(response)
        technical_summary = str(parsed.get("technical_summary", "")).strip()
        analysis_text = str(parsed.get("analysis_text", "")).strip()
        domain_status = str(parsed.get("domain_status", "generated")).strip() or "generated"
        plan_signal = str(parsed.get("plan_signal", "")).strip()
        action_status = str(parsed.get("action_status", "no_action_needed")).strip()
        action_type = str(parsed.get("action_type", "analyze")).strip()
        missing_inputs = parsed.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        pending_action = parsed.get("pending_action", {})
        if not isinstance(pending_action, dict):
            pending_action = {
                "kind": "none",
                "status": "no_action_needed",
                "missing_slots": [],
            }
        is_plan_context = self._is_training_plan_context(state)
        coach_text = technical_summary or analysis_text or response
        plan_text = technical_summary
        if is_plan_context and not self._has_material_training_summary(technical_summary):
            if not plan_signal:
                plan_signal = "insufficient_training_detail"
            domain_status = "insufficient_detail"
            plan_text = ""
        state.shared_context["training_analysis"] = {
            "status": domain_status,
            "text": plan_text,
            "plan_signal": plan_signal,
            "missing_inputs": missing_inputs,
            "action_status": action_status,
        }
        self._merge_persistence_candidates(
            state,
            memory_candidates=parsed.get("memory_candidates"),
            event_candidates=parsed.get("event_candidates"),
        )
        state.specialist_pending_actions["training_specialist"] = pending_action
        state.specialist_states["training_specialist"] = {
            "action_status": action_status,
            "action_type": action_type,
        }
        state.node_outputs["training_specialist"] = coach_text

    async def _node_nutrition_specialist(self, state: GraphState) -> None:
        peer_output = state.node_outputs.get("training_specialist", "")
        peer_block = f"\n\nANALISE_TREINO:\n{peer_output}" if peer_output else ""
        response = await self._run_llm_node(
            node_name="nutrition_specialist",
            state=state,
            extra_context=f"{self._shared_context_payload(state)}{peer_block}",
            allowed_tools=get_node_llm_tools("nutrition_specialist"),
        )
        parsed = self._parse_json_object(response)
        technical_summary = str(parsed.get("technical_summary", "")).strip()
        analysis_text = str(parsed.get("analysis_text", "")).strip()
        domain_status = str(parsed.get("domain_status", "generated")).strip() or "generated"
        plan_signal = str(parsed.get("plan_signal", "")).strip()
        action_status = str(parsed.get("action_status", "no_action_needed")).strip()
        action_type = str(parsed.get("action_type", "analyze")).strip()
        missing_inputs = parsed.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        pending_action = parsed.get("pending_action", {})
        if not isinstance(pending_action, dict):
            pending_action = {}
        coach_text = technical_summary or analysis_text or response
        plan_text = technical_summary
        state.shared_context["nutrition_analysis"] = {
            "status": domain_status,
            "text": plan_text,
            "plan_signal": plan_signal,
            "missing_inputs": missing_inputs,
            "action_status": action_status,
        }
        self._merge_persistence_candidates(
            state,
            memory_candidates=parsed.get("memory_candidates"),
            event_candidates=parsed.get("event_candidates"),
        )
        state.specialist_pending_actions["nutrition_specialist"] = pending_action
        state.specialist_states["nutrition_specialist"] = {
            "action_status": action_status,
            "action_type": action_type,
        }
        state.node_outputs["nutrition_specialist"] = coach_text

    async def _node_plan_specialist(self, state: GraphState) -> None:
        active_domain = state.conversation_state.get("active_domain", "general")
        input_data = state.shared_context.get("input_data", {})
        plan_section = input_data.get("plan_section", "")
        state.shared_context["has_active_plan"] = bool(plan_section)
        coordinator = await self._run_llm_node(
            node_name="plan_specialist",
            state=state,
            extra_context=(
                f"ANALISE_TREINO:\n{json.dumps(state.shared_context.get('training_analysis', {}), ensure_ascii=True, sort_keys=True)}\n\n"
                f"ANALISE_NUTRICAO:\n{json.dumps(state.shared_context.get('nutrition_analysis', {}), ensure_ascii=True, sort_keys=True)}"
            ),
            allowed_tools=get_node_llm_tools("plan_specialist"),
        )
        parsed = self._parse_json_object(coordinator)
        state.plan_needs_revision = bool(parsed.get("needs_revision", False))
        plan_status = str(parsed.get("plan_status", "")).strip()
        reason = str(parsed.get("reason", "")).strip()
        plan_candidate = str(parsed.get("plan_candidate", "")).strip()
        technical_summary = str(parsed.get("technical_summary", "")).strip()
        self._merge_persistence_candidates(
            state,
            memory_candidates=parsed.get("memory_candidates"),
            event_candidates=parsed.get("event_candidates"),
        )
        state.node_outputs["plan_specialist"] = technical_summary or (
            "Objetivo: gerenciar ciclo de vida do plano e consistencia entre treino e nutricao. "
            f"has_active_plan={state.shared_context['has_active_plan']}; "
            f"plan_status={plan_status}; revisao_necessaria={state.plan_needs_revision}; reason={reason}"
        )
        action_status = str(parsed.get("action_status", "no_action_needed")).strip()
        pending_slots = parsed.get("pending_slots", [])
        if not isinstance(pending_slots, list):
            pending_slots = []
        pending_action = parsed.get("pending_action", {})
        if not isinstance(pending_action, dict):
            pending_action = {}
        state.specialist_pending_actions["plan_specialist"] = pending_action
        state.specialist_states["plan_specialist"] = {
            "action_status": action_status,
            "pending_slots": pending_slots,
        }
        state.shared_context["plan_workspace"] = {
            "active_domain": active_domain,
            "has_active_plan": state.shared_context["has_active_plan"],
            "plan_status": plan_status,
            "needs_revision": state.plan_needs_revision,
            "reason": reason,
            "plan_candidate": plan_candidate,
            "lifecycle": state.shared_context.get("plan_lifecycle", {}),
            "training_preview": self._truncate(
                state.node_outputs.get("training_specialist", ""), 280
            ),
            "nutrition_preview": self._truncate(
                state.node_outputs.get("nutrition_specialist", ""), 280
            ),
        }

    async def _node_coach_reply(self, state: GraphState) -> None:
        if state.security_status != "safe":
            state.coach_response = self._blocked_response()
            state.node_outputs["coach_reply"] = state.coach_response
            return
        specialist_context = "\n\n".join(
            [
                self._shared_context_payload(state),
                state.node_outputs.get("training_specialist", ""),
                state.node_outputs.get("nutrition_specialist", ""),
                state.node_outputs.get("plan_specialist", ""),
            ]
        ).strip()
        response = await self._run_llm_node(
            node_name="coach_reply",
            state=state,
            extra_context=specialist_context,
            allowed_tools=get_node_llm_tools("coach_reply"),
        )
        public_text = response
        strip_wrappers = getattr(self._brain, "strip_internal_wrappers", None)
        if callable(strip_wrappers):
            public_text = strip_wrappers(response)
        state.coach_response = public_text
        state.response["technical"] = public_text
        state.final_response = public_text
        state.response["final"] = public_text
        state.node_outputs["coach_reply"] = public_text

    async def _node_memory_hub(self, state: GraphState) -> None:
        action_detail = "no_action"
        tools_by_name = {tool.name: tool for tool in self._brain.get_tools(state.user_email)}
        structured_candidates = dict(state.shared_context.get("persistence_candidates") or {})
        event_candidates = self._normalize_candidates(
            structured_candidates.get("event"), "event_action"
        )
        memory_candidates = self._normalize_candidates(
            structured_candidates.get("memory"), "memory_action"
        )
        if event_candidates and not self._has_unresolved_domain_pending_action(state):
            any_event = False
            for event_candidate in event_candidates:
                state.persistence_intents = event_candidate
                event_action = self._execute_event_intent(state, tools_by_name, event_candidate)
                if event_action:
                    any_event = True
                    self._log_persistence_decision(state, event_action)
            if any_event:
                return
        if memory_candidates:
            any_memory = False
            for memory_candidate in memory_candidates:
                state.persistence_intents = memory_candidate
                memory_action = self._execute_memory_intent(state, tools_by_name, memory_candidate)
                if memory_action:
                    any_memory = True
                    self._log_persistence_decision(state, memory_action)
            if any_memory:
                return
        planner = await self._run_llm_node(
            node_name="memory_hub",
            state=state,
            extra_context=(
                f"ANALISE_TECNICA:\n{state.coach_response}\n\n"
                f"ANALISE_TREINO:\n{state.node_outputs.get('training_specialist', '')}\n\n"
                f"ANALISE_NUTRICAO:\n{state.node_outputs.get('nutrition_specialist', '')}"
            ),
            allowed_tools=set(),
        )
        parsed = self._parse_json_object(planner)
        state.persistence_intents = parsed

        summary_update = parsed.get("summary_update") if isinstance(parsed, dict) else None
        if summary_update and isinstance(summary_update, str) and len(summary_update.strip()) > 10:
            snapshot = build_conversation_summary(summary_update)
            self._brain.add_system_message_to_history(state.user_email, snapshot)
            logger.info(
                "graph.summary_updated request_id=%s chars=%d",
                state.request_id, len(summary_update),
            )

        if not self._has_unresolved_domain_pending_action(state):
            event_action = self._execute_event_intent(state, tools_by_name, parsed)
            if event_action:
                self._log_persistence_decision(state, event_action)
                return
        memory_action = self._execute_memory_intent(state, tools_by_name, parsed)
        if memory_action:
            self._log_persistence_decision(state, memory_action)
            return
        state.node_outputs["memory_hub"] = "no_action"
        self._log_persistence_decision(state, action_detail)

    async def _run_llm_node(
        self,
        *,
        node_name: str,
        state: GraphState,
        allowed_tools: set[str],
        extra_context: str = "",
        message_override: str | None = None,
    ) -> str:
        cfg = self._registry.get_node_config(node_name)
        context_block = self._resolve_node_context(cfg, state)
        peer_block = self._resolve_peer_inputs(cfg, state)
        safe_prompt_text = self._escape_template_text(cfg.prompt_text)
        safe_context_block = self._escape_template_text(context_block)
        safe_peer_block = self._escape_template_text(peer_block)
        safe_output_contract = self._escape_template_text(cfg.output_contract)
        system_content = (
            f"{safe_prompt_text}\n\n"
            f"AVAILABLE_CONTEXT:\n{safe_context_block}\n\n"
            f"PEER_INPUTS:\n{safe_peer_block}\n\n"
            f"OUTPUT_CONTRACT:\n{safe_output_contract}"
        )
        if cfg.persona_mode == "none":
            system_content += (
                "\n\nPERSONA_RESTRICTION: Voce opera em modo analitico neutro. "
                "Nao adote a voz, tom, bordoes, girias ou maneirismos "
                "da persona do treinador. Sua saida deve ser tecnica, "
                "objetiva e impessoal. Se o contexto ou historico "
                "contiver mensagens com estilo de persona, ignore esse estilo."
            )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_content),
                ("human", "{user_message}"),
            ]
        )
        msg = message_override if message_override is not None else state.user_input_sanitized
        if extra_context:
            msg = f"{msg}\n\nCONTEXTO INTERNO:\n{extra_context}"
        shared_input = state.shared_context.get("input_data", {})
        input_data = {
            "user_message": msg,
            "user_locale": shared_input.get("user_locale", "pt-BR"),
            "prompt_name": f"graph:{node_name}",
            "session_id": state.user_email,
            "request_id": state.request_id,
            "conversation_id": state.conversation_id,
            "turn_id": state.turn_id,
            "node_name": node_name,
            "node_config_hash": cfg.config_hash,
            "context_blocks": cfg.context_blocks,
            "peer_inputs": cfg.peer_inputs,
            "persona_mode": cfg.persona_mode,
        }
        configured_tools = set(cfg.tool_names or [])
        effective_tools = allowed_tools & configured_tools if configured_tools else allowed_tools
        tools = [t for t in self._brain.get_tools(state.user_email) if t.name in effective_tools]
        chunks: list[str] = []
        response_format_arg = (
            cfg.response_format if isinstance(cfg.response_format, dict) else None
        )
        async for chunk in self._brain._llm_client.stream_with_tools(  # pylint: disable=protected-access
            prompt_template=prompt,
            input_data=input_data,
            tools=tools,
            user_email=state.user_email,
            log_callback=self._brain.get_log_callback(None),
            model_override=cfg.model_name,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            frequency_penalty=cfg.frequency_penalty,
            provider_sort=cfg.provider_sort,
            max_tokens=cfg.max_tokens,
            reasoning=cfg.reasoning,
            parallel_tool_calls=cfg.parallel_tool_calls,
            response_format=response_format_arg,
            run_name=f"graph.{node_name}",
            mode=f"graph:{node_name}",
        ):
            if isinstance(chunk, str):
                chunks.append(chunk)
            elif isinstance(chunk, dict) and chunk.get("type") == "tool_result":
                tool_name = str(chunk.get("tool_name", "unknown"))
                state.tools_called.append(tool_name)
                state.node_metadata.setdefault(node_name, {}).setdefault("tools_called", []).append(tool_name)
        return "".join(chunks).strip() or state.user_input_sanitized

    @staticmethod
    def _normalize_candidates(
        raw_candidates: Any,
        action_key: str,
    ) -> list[dict[str, Any]]:
        if not isinstance(raw_candidates, list):
            return []
        normalized: list[dict[str, Any]] = []
        for candidate in raw_candidates:
            if not isinstance(candidate, dict):
                continue
            action = str(candidate.get(action_key, "none")).strip().lower()
            if action in {"", "none"}:
                continue
            normalized.append(candidate)
        return normalized

    def _merge_persistence_candidates(
        self,
        state: GraphState,
        *,
        memory_candidates: Any = None,
        event_candidates: Any = None,
    ) -> None:
        bucket = state.shared_context.setdefault(
            "persistence_candidates",
            {"memory": [], "event": []},
        )
        bucket["memory"].extend(
            self._normalize_candidates(memory_candidates, "memory_action")
        )
        bucket["event"].extend(
            self._normalize_candidates(event_candidates, "event_action")
        )

    def _build_context_catalog(self, state: GraphState) -> dict[str, str]:
        input_data = state.shared_context.get("input_data", {})
        return {
            "request": state.user_input_sanitized or state.user_input_raw,
            "user_locale": str(input_data.get("user_locale", "pt-BR")),
            "current_date": str(input_data.get("current_date", "")),
            "user_profile": str(state.shared_context.get("user_profile_summary", "")),
            "trainer_identity": str(state.shared_context.get("trainer_identity", "")),
            "trainer_persona": str(state.shared_context.get("trainer_persona", "")),
            "agenda": str(state.shared_context.get("agenda_section", input_data.get("agenda_section", ""))),
            "active_plan": str(state.shared_context.get("plan_section", input_data.get("plan_section", ""))),
            "metabolism": str(state.shared_context.get("metabolism_section", input_data.get("metabolism_section", ""))),
            "history_summary": str(state.shared_context.get("history_summary", "")),
            "history_summary_neutral": str(
                state.shared_context.get(
                    "history_summary_neutral",
                    state.shared_context.get("history_summary", ""),
                )
            ),
            "conversation_summary": str(state.shared_context.get("conversation_summary", "")),
            "training_analysis": json.dumps(
                state.shared_context.get("training_analysis", {}),
                ensure_ascii=True,
                sort_keys=True,
            ),
            "nutrition_analysis": json.dumps(
                state.shared_context.get("nutrition_analysis", {}),
                ensure_ascii=True,
                sort_keys=True,
            ),
            "plan_workspace": str(state.shared_context.get("plan_workspace", "")),
            "plan_lifecycle": str(state.shared_context.get("plan_lifecycle", {})),
            "coach_response": str(state.coach_response),
            "security_result": str(state.security_status),
            "persistence_intents": str(state.persistence_intents),
            "conversation_state": json.dumps(
                state.conversation_state, ensure_ascii=True, sort_keys=True
            ),
        }

    def _resolve_node_context(self, cfg, state: GraphState) -> str:
        catalog = self._build_context_catalog(state)
        chunks = []
        for block in cfg.context_blocks:
            value = catalog.get(block, "")
            if value:
                chunks.append(f"[{block}]\n{value}")
        return "\n\n".join(chunks).strip() or "[empty]"

    def _resolve_peer_inputs(self, cfg, state: GraphState) -> str:
        chunks = []
        for node in cfg.peer_inputs:
            value = state.node_outputs.get(node, "")
            if value:
                chunks.append(f"[{node}]\n{value}")
        return "\n\n".join(chunks).strip() or "[none]"

    @staticmethod
    def _has_unresolved_domain_pending_action(state: GraphState) -> bool:
        """Return True when there's a domain execution pending_action that isn't resolved."""
        pa = state.conversation_state.get("pending_action", {})
        return (
            isinstance(pa, dict)
            and pa.get("kind") == "domain_execution"
            and pa.get("status") != "no_action_needed"
        )

    def _execute_event_intent(
        self,
        state: GraphState,
        tools_by_name: dict[str, Any],
        parsed: dict[str, Any],
    ) -> str | None:
        event_action = str(parsed.get("event_action", "none")).strip().lower()
        event_title = str(parsed.get("event_title", "")).strip()
        event_date = str(parsed.get("event_date", "")).strip()
        event_id = str(parsed.get("event_id", "")).strip()
        event_recurrence = str(
            parsed.get("event_recurrence", parsed.get("recurrence", ""))
        ).strip().lower()
        if event_recurrence not in {"weekly", "monthly"}:
            event_recurrence = "none"
        list_tool = tools_by_name.get("list_events")
        existing_events_dump = str(list_tool.invoke({})) if list_tool else ""
        if list_tool:
            state.tools_called.append("list_events")
        matched_event = self._find_matching_event(existing_events_dump, event_title, event_date)
        if not event_id and matched_event:
            event_id = matched_event["id"]
        normalized_date = self._normalize_event_date(event_date)
        if not normalized_date and event_date:
            inferred_recurrence = self._infer_event_recurrence(event_date)
            if event_recurrence == "none":
                event_recurrence = inferred_recurrence

        if normalized_date:
            event_date = normalized_date
        else:
            event_date = ""
            if event_recurrence == "none":
                event_recurrence = self._infer_event_recurrence(event_title)

        if event_action == "delete":
            delete_tool = tools_by_name.get("delete_event")
            if event_id and delete_tool:
                result = delete_tool.invoke({"event_id": event_id})
                state.persistence_actions.append(f"delete_event:{result}")
                state.tools_called.append("delete_event")
                state.node_outputs["memory_hub"] = "delete_event"
                return f"delete_event:{event_id}"
        if event_action == "update":
            update_tool = tools_by_name.get("update_event")
            payload: dict[str, Any] = {"event_id": event_id}
            if event_title:
                payload["title"] = event_title[:120]
            if event_date:
                payload["date"] = event_date
            if event_recurrence != "none":
                payload["recurrence"] = event_recurrence
            if event_id and update_tool and len(payload) > 1:
                result = update_tool.invoke(payload)
                state.persistence_actions.append(f"update_event:{result}")
                state.tools_called.append("update_event")
                state.node_outputs["memory_hub"] = "update_event"
                return f"update_event:{event_id}"
        if event_action == "create":
            if matched_event:
                update_tool = tools_by_name.get("update_event")
                payload: dict[str, Any] = {"event_id": matched_event["id"]}
                if event_title:
                    payload["title"] = event_title[:120]
                if event_date:
                    payload["date"] = event_date
                if update_tool and len(payload) > 1:
                    result = update_tool.invoke(payload)
                    state.persistence_actions.append(f"update_event:{result}")
                    state.tools_called.append("update_event")
                    state.node_outputs["memory_hub"] = "update_event"
                    return f"update_event:{matched_event['id']}"
            event_tool = tools_by_name.get("create_event")
            if event_tool and event_title:
                payload = {"title": event_title[:120]}
                if event_date:
                    payload["date"] = event_date
                if event_recurrence != "none":
                    payload["recurrence"] = event_recurrence
                result = event_tool.invoke(payload)
                state.persistence_actions.append(f"create_event:{result}")
                state.tools_called.append("create_event")
                state.node_outputs["memory_hub"] = "create_event"
                return "create_event:title"
        return None

    def _execute_memory_intent(
        self,
        state: GraphState,
        tools_by_name: dict[str, Any],
        parsed: dict[str, Any],
    ) -> str | None:
        memory_action = str(parsed.get("memory_action", "none")).strip().lower()
        memory_content = str(parsed.get("memory_content", "")).strip()
        memory_id = str(parsed.get("memory_id", "")).strip()
        memory_category = str(parsed.get("memory_category", "context")).strip() or "context"
        search_tool = tools_by_name.get("search_memory")
        existing_memories_dump = ""
        if search_tool and memory_content:
            existing_memories_dump = str(
                search_tool.invoke({"query": memory_content[:80], "limit": 3})
            )
            state.tools_called.append("search_memory")
        if not memory_id:
            memory_id = self._extract_memory_id(existing_memories_dump) or ""

        if memory_action == "update":
            update_memory_tool = tools_by_name.get("update_memory")
            if update_memory_tool and memory_id and memory_content:
                result = update_memory_tool.invoke(
                    {"memory_id": memory_id, "new_content": memory_content[:280]}
                )
                state.persistence_actions.append(f"update_memory:{result}")
                state.tools_called.append("update_memory")
                state.node_outputs["memory_hub"] = "update_memory"
                return f"update_memory:{memory_id}"
        if memory_action == "save":
            if memory_id:
                update_memory_tool = tools_by_name.get("update_memory")
                if update_memory_tool and memory_content:
                    result = update_memory_tool.invoke(
                        {"memory_id": memory_id, "new_content": memory_content[:280]}
                    )
                    state.persistence_actions.append(f"update_memory:{result}")
                    state.tools_called.append("update_memory")
                    state.node_outputs["memory_hub"] = "update_memory"
                    return f"update_memory:{memory_id}"
            memory_tool = tools_by_name.get("save_memory")
            if memory_tool and memory_content:
                result = memory_tool.invoke(
                    {"content": memory_content[:280], "category": memory_category}
                )
                state.persistence_actions.append(f"save_memory:{result}")
                state.tools_called.append("save_memory")
                state.node_outputs["memory_hub"] = "save_memory"
                return "save_memory:new"
        return None

    @staticmethod
    def _truncate(text: str, max_chars: int) -> str:
        if len(text) <= max_chars:
            return text
        return f"{text[:max_chars]}..."

    def _shared_context_payload(self, state: GraphState) -> str:
        input_data = state.shared_context.get("input_data", {})
        runtime_json = str(input_data.get("runtime_context_json", ""))
        plan_section = str(input_data.get("plan_section", ""))
        agenda_section = str(input_data.get("agenda_section", ""))
        metabolism_section = str(input_data.get("metabolism_section", ""))
        payload = (
            f"RUNTIME_CONTEXT_JSON:\n{self._truncate(runtime_json, 4000)}\n\n"
            f"PLAN_SECTION:\n{self._truncate(plan_section, 1200)}\n\n"
            f"AGENDA_SECTION:\n{self._truncate(agenda_section, 1200)}\n\n"
            f"METABOLISM_SECTION:\n{self._truncate(metabolism_section, 1200)}\n\n"
            f"PLAN_LIFECYCLE:\n{state.shared_context.get('plan_lifecycle', {})}"
        )
        return payload

    def _log_persistence_decision(self, state: GraphState, action_detail: str) -> None:
        logger.info(
            "graph.persistence_decision request_id=%s turn_id=%s action=%s tools=%s",
            state.request_id,
            state.turn_id,
            action_detail,
            state.tools_called,
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.lower().split())

    def _find_matching_event(
        self,
        events_dump: str,
        title: str,
        date: str,
    ) -> dict[str, str] | None:
        normalized_title = self._normalize_text(title)
        normalized_date = self._normalize_text(date)
        for match in _EVENT_LINE_PATTERN.finditer(events_dump):
            candidate_title = self._normalize_text(match.group("title"))
            candidate_date = self._normalize_text(match.group("date"))
            title_match = normalized_title and (
                normalized_title in candidate_title or candidate_title in normalized_title
            )
            date_match = not normalized_date or normalized_date == candidate_date
            if title_match and date_match:
                return {
                    "id": match.group("id"),
                    "title": match.group("title"),
                    "date": match.group("date"),
                }
        return None

    @staticmethod
    def _blocked_response() -> str:
        return (
            "Nao posso revelar instrucoes internas nem dados de sistema. "
            "Posso ajudar com treino, nutricao e plano."
        )

    @staticmethod
    def _extract_event_id(text: str) -> str | None:
        match = _EVENT_ID_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _extract_memory_id(text: str) -> str | None:
        match = _MEMORY_ID_PATTERN.search(text)
        return match.group(1) if match else None

    @staticmethod
    def _parse_json_object(raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            snippet = text[start : end + 1]
            try:
                return json.loads(snippet)
            except json.JSONDecodeError:
                return {}
        return {}
