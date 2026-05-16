"""Conversation graph runtime."""

from __future__ import annotations

import asyncio
import copy
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
_TRAINING_SPECIALIST_OWNED_SLOTS = {
    "exercise_sets",
    "exercise_reps",
    "load_guidance",
    "rest_guidance",
    "progression_scheme",
}
_NUTRITION_SPECIALIST_OWNED_SLOTS = {
    "calories",
    "protein_target",
    "carb_target",
    "fat_target",
    "macro_split",
    "adherence_strategy",
}
_SPECIALIST_DELEGATION_PATTERNS = [
    r"\bdecid[ea]\s+voce\b",
    r"\bdecide\s+voce\b",
    r"\bvoc[eê]\s+[ée]\s+meu\s+treinador\b",
    r"\bfaz\s+do\s+jeito\s+que\s+voc[eê]\s+achar\s+melhor\b",
    r"\bdo\s+what\s+you\s+think\s+is\s+best\b",
    r"\byou\s+are\s+my\s+trainer\b",
]
_ACTION_STATUS_ALIASES = {
    "success": ActionStatus.EXECUTED.value,
    "succeeded": ActionStatus.EXECUTED.value,
    "complete": ActionStatus.EXECUTED.value,
    "completed": ActionStatus.EXECUTED.value,
    "error": ActionStatus.FAILED.value,
}
_TRAINING_PERSISTENCE_STATUS_TOKENS = {
    "plan_updated",
    "updated",
    "routine_updated",
    "training_program_updated",
}
_TRAINING_PERSISTENCE_TEXT_PATTERNS = [
    r"\bsubstitu[íi]\b",
    r"\batualizei\b",
    r"\btroquei\b",
    r"\bsalvei\b",
    r"\bpersisti\b",
    r"\breplacei\b",
    r"\bupdated\b",
    r"\bsaved\b",
]


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
    last_raw_outputs: dict[str, str] = field(default_factory=dict)
    node_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    plan_needs_revision: bool = False
    persistence_intents: dict[str, Any] = field(default_factory=dict)
    conversation_state: dict[str, Any] = field(default_factory=default_conversation_state)
    specialist_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    specialist_pending_actions: dict[str, dict[str, Any]] = field(default_factory=dict)
    specialist_results: dict[str, dict[str, Any]] = field(default_factory=dict)
    coach_handoff: list[dict[str, Any]] = field(default_factory=list)
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
            "specialist_results": self.specialist_results,
            "coach_handoff": self.coach_handoff,
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
        conversation_state_before = copy.deepcopy(state.conversation_state)

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
                        conversation_state_before=conversation_state_before,
                    ),
                )

    def _resolve_pending_actions(self, state: GraphState) -> None:
        """Merge specialist pending_action suggestions using priority."""
        merged = resolve_pending_action(state.specialist_pending_actions)
        merged = self._sanitize_pending_action_payload(merged)
        last_action = ActionStatus.NO_ACTION_NEEDED.value
        observed_statuses: list[str] = []
        for node_name in ("training_specialist", "nutrition_specialist", "plan_specialist"):
            spec = state.specialist_states.get(node_name, {})
            status = spec.get("action_status", "")
            if status:
                observed_statuses.append(status)
        if ActionStatus.FAILED.value in observed_statuses:
            last_action = ActionStatus.FAILED.value
        elif ActionStatus.EXECUTED.value in observed_statuses:
            last_action = ActionStatus.EXECUTED.value
        elif ActionStatus.NEEDS_USER_INPUT.value in observed_statuses:
            last_action = ActionStatus.NEEDS_USER_INPUT.value
        state.conversation_state["pending_action"] = merged
        state.conversation_state["last_action_status"] = last_action
        active_domain = self._derive_active_domain(state)
        state.conversation_state["active_domain"] = active_domain
        state.routing["intent"] = active_domain

    @staticmethod
    def _specialist_owned_slots(domain: str) -> set[str]:
        if domain == "training":
            return set(_TRAINING_SPECIALIST_OWNED_SLOTS)
        if domain == "nutrition":
            return set(_NUTRITION_SPECIALIST_OWNED_SLOTS)
        return set()

    @classmethod
    def _are_only_specialist_owned_slots(
        cls,
        domain: str,
        slots: list[str],
    ) -> bool:
        normalized = [str(slot).strip() for slot in slots if str(slot).strip()]
        if not normalized:
            return False
        owned = cls._specialist_owned_slots(domain)
        return all(slot in owned for slot in normalized)

    @classmethod
    def _sanitize_pending_action_payload(cls, pending_action: dict[str, Any]) -> dict[str, Any]:
        sanitized = cls._normalize_pending_action(pending_action)
        slots = sanitized.get("missing_slots", [])
        if (
            sanitized.get("kind") == "plan_review"
            and (
                cls._are_only_specialist_owned_slots("training", slots)
                or cls._are_only_specialist_owned_slots("nutrition", slots)
            )
        ):
            return {
                "kind": "none",
                "status": "no_action_needed",
                "missing_slots": [],
            }
        return sanitized

    @classmethod
    def _sanitize_conversation_state_payload(cls, payload: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return default_conversation_state()
        sanitized = copy.deepcopy(payload)
        pending_action = cls._sanitize_pending_action_payload(
            sanitized.get("pending_action", {})
        )
        sanitized["pending_action"] = pending_action
        if pending_action.get("kind") == "none":
            last_action = str(sanitized.get("last_action_status", "")).strip()
            if last_action == ActionStatus.NEEDS_USER_INPUT.value:
                sanitized["last_action_status"] = ActionStatus.NO_ACTION_NEEDED.value
        if not sanitized.get("active_domain"):
            sanitized["active_domain"] = "general"
        return sanitized

    @staticmethod
    def _user_delegated_specialist_decision(message: str) -> bool:
        lowered = message.lower()
        return any(re.search(pattern, lowered) for pattern in _SPECIALIST_DELEGATION_PATTERNS)

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

        runtime_config = {
            "temperature": cfg.temperature,
            "max_tokens": cfg.max_tokens,
            "top_p": cfg.top_p,
            "frequency_penalty": cfg.frequency_penalty,
            "provider_sort": cfg.provider_sort,
            "tool_policy": cfg.tool_policy,
            "tool_names": list(cfg.tool_names),
            "parallel_tool_calls": cfg.parallel_tool_calls,
            "reasoning": cfg.reasoning,
            "context_blocks": list(cfg.context_blocks),
            "peer_inputs": list(cfg.peer_inputs),
            "output_contract": cfg.output_contract,
        }

        resolved_ctx = self._resolve_node_context(cfg, state)
        resolved_peers = self._resolve_peer_inputs(cfg, state)
        resolved_data = {
            "resolved_input": state.request.get("sanitized_input", state.user_input_raw),
            "resolved_context": self._truncate(resolved_ctx, 4000),
            "resolved_peer_outputs": self._truncate(resolved_peers, 4000),
        }

        state.node_metadata[node_name] = {
            **base_meta,
            **runtime_config,
            **resolved_data,
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

        state.node_metadata[node_name]["state_before"] = self._capture_state_snapshot(state)

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
            state_after = self._capture_state_snapshot(state)
            state_before_snap = state.node_metadata[node_name].get("state_before", {})
            state.node_metadata[node_name]["state_after"] = state_after
            state.node_metadata[node_name]["state_diff"] = self._compute_state_diff(
                state_before_snap,
                state_after,
            )
            raw = state.last_raw_outputs.get(node_name, "")
            state.node_metadata[node_name]["raw_output"] = self._truncate(raw, 8000) if raw else ""
            state.node_metadata[node_name]["structured_output"] = self._try_parse_json(raw)
            if node_name in state.specialist_states:
                state.node_metadata[node_name]["specialist_state"] = copy.deepcopy(
                    state.specialist_states[node_name]
                )
            if node_name in state.specialist_pending_actions:
                state.node_metadata[node_name]["pending_action"] = copy.deepcopy(
                    state.specialist_pending_actions[node_name]
                )
            if node_name in state.specialist_results:
                state.node_metadata[node_name]["specialist_result"] = copy.deepcopy(
                    state.specialist_results[node_name]
                )
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

    @staticmethod
    def _capture_state_snapshot(state: GraphState) -> dict[str, Any]:
        snapshot_keys = [
            "conversation_state",
            "specialist_states",
            "specialist_pending_actions",
            "specialist_results",
            "coach_handoff",
            "tools_called",
            "persistence_actions",
            "plan_needs_revision",
            "security_status",
            "response",
            "node_outputs",
        ]
        result: dict[str, Any] = {}
        for key in snapshot_keys:
            result[key] = copy.deepcopy(getattr(state, key, None))
        shared_keys = [
            "training_analysis", "nutrition_analysis", "plan_workspace",
            "persistence_candidates", "has_active_plan", "history_summary_neutral",
        ]
        result["shared_context"] = {
            k: copy.deepcopy(state.shared_context.get(k, None))
            for k in shared_keys
        }
        return result

    @staticmethod
    def _compute_state_diff(before: dict, after: dict) -> dict[str, Any]:
        diff: dict[str, Any] = {"added": {}, "removed": {}, "changed": {}}
        all_keys = set(before) | set(after)
        for key in all_keys:
            if key not in before:
                diff["added"][key] = copy.deepcopy(after.get(key))
            elif key not in after:
                diff["removed"][key] = copy.deepcopy(before.get(key))
            elif before.get(key) != after.get(key):
                diff["changed"][key] = {
                    "before": copy.deepcopy(before.get(key)),
                    "after": copy.deepcopy(after.get(key)),
                }
        return diff

    @staticmethod
    def _try_parse_json(text: str) -> Any | None:
        if not text or not text.strip():
            return None
        stripped = text.strip()
        if not stripped.startswith(("{", "[")):
            return None
        try:
            return json.loads(stripped)
        except (json.JSONDecodeError, ValueError):
            return None

    @staticmethod
    def _default_operation_result() -> dict[str, Any]:
        return {
            "attempted": False,
            "succeeded": False,
            "tool_name": "",
            "error_code": "",
            "evidence": "",
        }

    @classmethod
    def _normalize_operation_result(cls, raw: Any) -> dict[str, Any]:
        result = cls._default_operation_result()
        if isinstance(raw, dict):
            result["attempted"] = bool(raw.get("attempted", False))
            result["succeeded"] = bool(raw.get("succeeded", False))
            result["tool_name"] = str(
                raw.get("tool_name", raw.get("action_name", ""))
            ).strip()
            result["error_code"] = str(raw.get("error_code", "")).strip()
            result["evidence"] = str(
                raw.get("evidence", raw.get("details", ""))
            ).strip()
        return result

    @staticmethod
    def _normalize_action_status(raw: Any) -> tuple[str, bool]:
        status = str(raw or "").strip().lower()
        allowed = {
            ActionStatus.EXECUTED.value,
            ActionStatus.FAILED.value,
            ActionStatus.NEEDS_USER_INPUT.value,
            ActionStatus.NO_ACTION_NEEDED.value,
        }
        if status in allowed:
            return status, False
        alias = _ACTION_STATUS_ALIASES.get(status)
        if alias:
            return alias, True
        return ActionStatus.FAILED.value, True

    @staticmethod
    def _normalize_plan_payload(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return {}
        return copy.deepcopy(raw)

    @classmethod
    def _extract_plan_signal_and_payload(cls, parsed: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        raw_signal = parsed.get("plan_signal", "")
        if isinstance(raw_signal, dict):
            signal = str(raw_signal.get("type", "")).strip()
            payload = cls._normalize_plan_payload(raw_signal.get("payload"))
            return signal, payload
        signal = str(raw_signal).strip()
        payload = cls._normalize_plan_payload(parsed.get("plan_payload"))
        return signal, payload

    @staticmethod
    def _has_structured_training_plan_payload(payload: dict[str, Any]) -> bool:
        if not isinstance(payload, dict) or not payload:
            return False
        change_type = str(payload.get("change_type", "")).strip().lower()
        if change_type == "exercise_replacement":
            routine_name = str(payload.get("routine_name", "")).strip()
            old_exercise = str(payload.get("old_exercise", "")).strip()
            new_exercise = payload.get("new_exercise", {})
            if not isinstance(new_exercise, dict):
                return False
            new_name = str(new_exercise.get("name", "")).strip()
            sets = new_exercise.get("sets")
            reps = str(new_exercise.get("reps", "")).strip()
            effort = str(new_exercise.get("rpe", new_exercise.get("rir", ""))).strip()
            rest = str(new_exercise.get("rest", "")).strip()
            return bool(
                routine_name and old_exercise and new_name and sets and reps and (effort or rest)
            )
        return False

    @staticmethod
    def _training_claimed_plan_persistence(
        domain_status: str,
        public_message: str,
        internal_analysis: str,
        operation_result: dict[str, Any],
    ) -> bool:
        tool_name = str(operation_result.get("tool_name", "")).strip().lower()
        if tool_name == "upsert_plan":
            return False
        if domain_status.strip().lower() in _TRAINING_PERSISTENCE_STATUS_TOKENS:
            return True
        text = " ".join([public_message, internal_analysis]).lower()
        return any(re.search(pattern, text) for pattern in _TRAINING_PERSISTENCE_TEXT_PATTERNS)

    @staticmethod
    def _operation_result_from_tool_results(
        state: GraphState,
        node_name: str,
        tool_name: str,
    ) -> dict[str, Any] | None:
        tool_results = state.node_metadata.get(node_name, {}).get("tool_results", [])
        if not isinstance(tool_results, list):
            return None
        matching = [
            result
            for result in tool_results
            if isinstance(result, dict) and result.get("tool_name") == tool_name
        ]
        if not matching:
            return None

        last_result = matching[-1]
        content = str(last_result.get("content", ""))
        status = str(last_result.get("status", "")).strip().lower()
        error_match = re.search(r"\bERRO_[A-Z0-9_]+\b", content)
        error_code = error_match.group(0) if error_match else ""
        evidence = ""
        if "PLANO_NAO_SALVO" in content:
            evidence = "PLANO_NAO_SALVO"
        elif error_code:
            evidence = "TOOL_ERROR"

        failed = bool(error_code or evidence == "PLANO_NAO_SALVO" or status in {"error", "failed"})
        succeeded = "PLANO_SALVO" in content or status in {"success", "succeeded", "ok"}
        if not failed and not succeeded:
            return None
        return {
            "attempted": True,
            "succeeded": succeeded and not failed,
            "tool_name": tool_name,
            "error_code": error_code,
            "evidence": evidence or ("PLANO_SALVO" if succeeded else ""),
        }

    @staticmethod
    def _normalize_pending_action(raw: Any) -> dict[str, Any]:
        if isinstance(raw, dict):
            missing_slots = raw.get("missing_slots", [])
            if not isinstance(missing_slots, list):
                missing_slots = []
            return {
                "kind": str(raw.get("kind", "none")).strip() or "none",
                "status": str(raw.get("status", "no_action_needed")).strip() or "no_action_needed",
                "missing_slots": [str(item) for item in missing_slots],
            }
        return {
            "kind": "none",
            "status": "no_action_needed",
            "missing_slots": [],
        }

    @classmethod
    def _record_specialist_result(
        cls,
        state: GraphState,
        node_name: str,
        parsed: dict[str, Any],
        domain_status: str,
        plan_signal: str,
        pending_action: dict[str, Any],
    ) -> dict[str, Any]:
        missing_inputs = parsed.get("missing_inputs", parsed.get("pending_slots", []))
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        action_status = str(parsed.get("action_status", "no_action_needed")).strip() or "no_action_needed"
        action_type = str(parsed.get("action_type", parsed.get("plan_status", "analyze"))).strip() or "analyze"
        public_message = str(parsed.get("public_message", "")).strip()
        internal_analysis = str(
            parsed.get(
                "internal_analysis",
                parsed.get("technical_summary", parsed.get("analysis_text", "")),
            )
        ).strip()
        operation_result = cls._normalize_operation_result(parsed.get("operation_result"))
        if (
            action_status == ActionStatus.EXECUTED.value
            and operation_result["attempted"]
            and not operation_result["succeeded"]
        ):
            action_status = ActionStatus.FAILED.value
            if not public_message:
                public_message = "Nao consegui concluir a acao solicitada; ela nao foi salva."
        result = {
            "node_name": node_name,
            "action_status": action_status,
            "action_type": action_type,
            "domain_status": domain_status,
            "public_message": public_message,
            "internal_analysis": internal_analysis,
            "missing_inputs": [str(item) for item in missing_inputs],
            "plan_signal": plan_signal,
            "plan_payload": copy.deepcopy(parsed.get("plan_payload", {}))
            if isinstance(parsed.get("plan_payload"), dict)
            else {},
            "pending_action": pending_action,
            "operation_result": operation_result,
        }
        state.specialist_results[node_name] = result
        state.specialist_states[node_name] = {
            "action_status": action_status,
            "action_type": action_type,
        }
        state.specialist_pending_actions[node_name] = pending_action
        return result

    @staticmethod
    def _append_coach_handoff(
        state: GraphState,
        node_name: str,
        label: str,
        result: dict[str, Any],
    ) -> None:
        public_message = str(result.get("public_message", "")).strip()
        if not public_message:
            return
        state.coach_handoff.append(
            {
                "source": node_name,
                "label": label,
                "action_status": result.get("action_status", ""),
                "public_message": public_message,
                "operation_result": result.get(
                    "operation_result",
                    ConversationGraphRunner._default_operation_result(),
                ),
            }
        )

    @staticmethod
    def _has_failed_material_operation(state: GraphState) -> bool:
        return any(
            result.get("operation_result", {}).get("attempted") is True
            and result.get("operation_result", {}).get("succeeded") is False
            for result in state.specialist_results.values()
        )

    def _build_timeline_summary(self, state: GraphState) -> dict:
        slowest = None
        largest = None
        state_changed_nodes: list[str] = []
        pending_nodes: list[str] = []
        interrupted_at: str | None = None
        max_duration: float = -1
        max_output_len: int = -1
        for node_name in self.NODE_ORDER:
            meta = state.node_metadata.get(node_name, {})
            status = meta.get("status", "")
            duration = meta.get("duration_ms")
            if isinstance(duration, (int, float)) and duration > max_duration:
                max_duration = duration
                slowest = node_name
            raw_text = meta.get("raw_output", "")
            if isinstance(raw_text, str) and len(raw_text) > max_output_len:
                max_output_len = len(raw_text)
                largest = node_name
            state_diff = meta.get("state_diff", {})
            if isinstance(state_diff, dict) and (
                state_diff.get("added") or state_diff.get("changed") or state_diff.get("removed")
            ):
                state_changed_nodes.append(node_name)
            pa = meta.get("pending_action", {})
            if isinstance(pa, dict) and pa.get("kind") not in (None, "none", ""):
                pending_nodes.append(node_name)
            if status == "failed" and interrupted_at is None:
                interrupted_at = node_name
        return {
            "slowest_node": slowest,
            "largest_output_node": largest,
            "largest_output_chars": max_output_len if max_output_len > 0 else None,
            "nodes_with_state_changes": state_changed_nodes,
            "nodes_with_pending_actions": pending_nodes,
            "interrupted_at": interrupted_at,
        }

    def _build_debug_trace(
        self,
        *,
        state: GraphState,
        started_at: datetime,
        ended_at: datetime,
        graph_error: str | None,
        conversation_state_before: dict | None = None,
    ) -> dict[str, Any]:
        nodes: list[dict[str, Any]] = []
        for node_name in self.NODE_ORDER:
            meta = dict(state.node_metadata.get(node_name, {}))
            node_entry: dict[str, Any] = {
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
                "temperature": meta.get("temperature"),
                "max_tokens": meta.get("max_tokens"),
                "top_p": meta.get("top_p"),
                "frequency_penalty": meta.get("frequency_penalty"),
                "provider_sort": meta.get("provider_sort"),
                "tool_policy": meta.get("tool_policy"),
                "tool_names": meta.get("tool_names", []),
                "parallel_tool_calls": meta.get("parallel_tool_calls"),
                "reasoning": meta.get("reasoning"),
                "context_blocks": meta.get("context_blocks", []),
                "peer_inputs": meta.get("peer_inputs", []),
                "output_contract": meta.get("output_contract", ""),
                "resolved_input": meta.get("resolved_input", ""),
                "resolved_context": meta.get("resolved_context", ""),
                "resolved_peer_outputs": meta.get("resolved_peer_outputs", ""),
                "raw_output": meta.get("raw_output", ""),
                "structured_output": meta.get("structured_output"),
                "state_before": meta.get("state_before"),
                "state_after": meta.get("state_after"),
                "state_diff": meta.get("state_diff"),
                "specialist_state": meta.get("specialist_state"),
                "specialist_result": meta.get("specialist_result"),
                "pending_action": meta.get("pending_action"),
            }
            nodes.append(node_entry)
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
            "specialist_results": copy.deepcopy(state.specialist_results),
            "coach_handoff": copy.deepcopy(state.coach_handoff),
            "nodes": nodes,
            "graph_error": graph_error,
            "request_payload_sanitized": state.request.get("sanitized_input", ""),
            "conversation_state_before": conversation_state_before or {},
            "conversation_state_after": copy.deepcopy(state.conversation_state),
            "pending_action_resolution": state.conversation_state.get("pending_action", {}),
            "timeline_summary": self._build_timeline_summary(state),
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
            state.conversation_state = self._sanitize_conversation_state_payload(previous_state)
        if self._user_delegated_specialist_decision(
            state.user_input_sanitized or state.user_input_raw
        ):
            state.conversation_state = self._sanitize_conversation_state_payload(
                state.conversation_state
            )
            pending_action = state.conversation_state.get("pending_action", {})
            slots = pending_action.get("missing_slots", []) if isinstance(pending_action, dict) else []
            if (
                self._are_only_specialist_owned_slots("training", slots)
                or self._are_only_specialist_owned_slots("nutrition", slots)
            ):
                state.conversation_state["pending_action"] = {
                    "kind": "none",
                    "status": "no_action_needed",
                    "missing_slots": [],
                }
                if state.conversation_state.get("last_action_status") == ActionStatus.NEEDS_USER_INPUT.value:
                    state.conversation_state["last_action_status"] = ActionStatus.NO_ACTION_NEEDED.value
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

        classifier = ""
        try:
            classifier = await self._run_llm_node(
                node_name="prompt_security",
                state=state,
                allowed_tools=set(),
                message_override=state.user_input_raw,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            logger.warning(
                "graph.prompt_security_llm_failed request_id=%s turn_id=%s",
                state.request_id,
                state.turn_id,
                exc_info=True,
            )

        if not classifier or not classifier.strip():
            state.security_status = "blocked"
            state.user_input_sanitized = ""
            state.blocked_segments.append("llm_unavailable")
            state.node_outputs["prompt_security"] = "blocked:llm_unavailable"
            logger.warning(
                "graph.prompt_security_blocked request_id=%s turn_id=%s reason=llm_unavailable",
                state.request_id,
                state.turn_id,
            )
            return

        parsed = self._parse_json_object(classifier)
        status = str(parsed.get("status", "safe")).lower()
        if status not in {"safe", "blocked"}:
            status = "safe"

        if not parsed or (status == "safe" and not str(parsed.get("sanitized", "")).strip()):
            logger.warning(
                "graph.prompt_security_empty_parsed request_id=%s turn_id=%s using_raw",
                state.request_id,
                state.turn_id,
            )

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
        base_extra_context = f"{self._shared_context_payload(state)}{peer_block}"
        response = await self._run_llm_node(
            node_name="training_specialist",
            state=state,
            extra_context=base_extra_context,
            allowed_tools=get_node_llm_tools("training_specialist"),
        )
        parsed = self._parse_json_object(response)
        domain_status = str(parsed.get("domain_status", "generated")).strip() or "generated"
        plan_signal, plan_payload = self._extract_plan_signal_and_payload(parsed)
        action_status, action_status_normalized = self._normalize_action_status(
            parsed.get("action_status", "no_action_needed")
        )
        action_type = str(parsed.get("action_type", "analyze")).strip()
        public_message = str(parsed.get("public_message", "")).strip()
        internal_analysis = str(
            parsed.get(
                "internal_analysis",
                parsed.get("technical_summary", parsed.get("analysis_text", "")),
            )
        ).strip()
        operation_result = self._normalize_operation_result(parsed.get("operation_result"))
        is_plan_context = self._is_training_plan_context(state)
        if action_status_normalized and action_status == ActionStatus.FAILED.value and not public_message:
            public_message = "A saida do especialista de treino ficou invalida para este contrato."
        if is_plan_context and self._training_claimed_plan_persistence(
            domain_status,
            public_message,
            internal_analysis,
            operation_result,
        ):
            if domain_status.lower() in _TRAINING_PERSISTENCE_STATUS_TOKENS:
                domain_status = "generated"
            if action_type.lower() in {"update_plan", "plan_update"}:
                action_type = "analyze_plan_change"
            public_message = ""
        missing_inputs = parsed.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        pending_action = self._normalize_pending_action(parsed.get("pending_action"))
        invalid_specialist_owned_question = (
            action_status == ActionStatus.NEEDS_USER_INPUT.value
            and self._are_only_specialist_owned_slots(
                "training",
                pending_action.get("missing_slots", missing_inputs) or missing_inputs,
            )
        )
        if invalid_specialist_owned_question and self._is_training_plan_context(state):
            retry_response = await self._run_llm_node(
                node_name="training_specialist",
                state=state,
                extra_context=(
                    f"{base_extra_context}\n\n"
                    "RUNTIME_CORRECTION:\n"
                    "Your previous output asked the user for specialist-owned training parameters. "
                    "This is invalid. Decide sets, reps, load guidance, rest guidance, and progression "
                    "yourself from the active plan, history, and tool context. Return material "
                    "internal_analysis and do not ask the user for those parameters."
                ),
                allowed_tools=get_node_llm_tools("training_specialist"),
            )
            retry_parsed = self._parse_json_object(retry_response)
            if retry_parsed:
                parsed = retry_parsed
                domain_status = str(parsed.get("domain_status", "generated")).strip() or "generated"
                plan_signal, plan_payload = self._extract_plan_signal_and_payload(parsed)
                action_status, action_status_normalized = self._normalize_action_status(
                    parsed.get("action_status", "no_action_needed")
                )
                action_type = str(parsed.get("action_type", "analyze")).strip()
                public_message = str(parsed.get("public_message", "")).strip()
                internal_analysis = str(
                    parsed.get(
                        "internal_analysis",
                        parsed.get("technical_summary", parsed.get("analysis_text", "")),
                    )
                ).strip()
                operation_result = self._normalize_operation_result(parsed.get("operation_result"))
                if action_status_normalized and action_status == ActionStatus.FAILED.value and not public_message:
                    public_message = "A saida do especialista de treino ficou invalida para este contrato."
                if is_plan_context and self._training_claimed_plan_persistence(
                    domain_status,
                    public_message,
                    internal_analysis,
                    operation_result,
                ):
                    if domain_status.lower() in _TRAINING_PERSISTENCE_STATUS_TOKENS:
                        domain_status = "generated"
                    if action_type.lower() in {"update_plan", "plan_update"}:
                        action_type = "analyze_plan_change"
                    public_message = ""
                missing_inputs = parsed.get("missing_inputs", [])
                if not isinstance(missing_inputs, list):
                    missing_inputs = []
                pending_action = self._normalize_pending_action(parsed.get("pending_action"))
            invalid_specialist_owned_question = (
                action_status == ActionStatus.NEEDS_USER_INPUT.value
                and self._are_only_specialist_owned_slots(
                    "training",
                    pending_action.get("missing_slots", missing_inputs) or missing_inputs,
                )
            )
        tools_called = state.node_metadata.get("training_specialist", {}).get("tools_called", [])
        if (
            action_type == "execute_routine"
            and action_status == "executed"
            and not tools_called
        ):
            action_status = "failed"
            domain_status = "insufficient_detail"
            plan_signal = plan_signal or "missing_execution_evidence"
            operation_result = {
                "attempted": True,
                "succeeded": False,
                "tool_name": "",
                "error_code": "MISSING_TOOL_EVIDENCE",
                "evidence": "NO_TOOL_CALL_RECORDED",
            }
            public_message = public_message or (
                "Nao consegui criar ou atualizar a rotina porque nenhuma ferramenta confirmou a acao."
            )
            internal_analysis = (
                "Ação de treino declarou execução sem evidência de tool neste turno. "
                "Confirmação adicional é necessária."
            )
        if invalid_specialist_owned_question:
            action_status = ActionStatus.FAILED.value
            domain_status = "specialist_role_violation"
            plan_signal = plan_signal or "specialist_role_violation"
            public_message = ""
            internal_analysis = (
                "Training specialist requested specialist-owned technical parameters from the "
                "user during plan review. This violates decision ownership."
            )
            missing_inputs = []
            plan_payload = {}
            pending_action = {
                "kind": "none",
                "status": "no_action_needed",
                "missing_slots": [],
            }
        plan_text = internal_analysis
        if (
            is_plan_context
            and domain_status != "specialist_role_violation"
            and not (
                self._has_material_training_summary(internal_analysis)
                or self._has_structured_training_plan_payload(plan_payload)
            )
        ):
            if not plan_signal:
                plan_signal = "insufficient_training_detail"
            domain_status = "insufficient_detail"
            plan_text = ""
            internal_analysis = ""
            plan_payload = {}
            if action_status != "no_action_needed":
                public_message = public_message or (
                    "A contribuicao de treino ainda esta insuficiente para criar ou revisar o plano com seguranca."
                )
        state.shared_context["training_analysis"] = {
            "status": domain_status,
            "text": plan_text,
            "plan_signal": plan_signal,
            "plan_payload": copy.deepcopy(plan_payload),
            "missing_inputs": missing_inputs,
            "action_status": action_status,
        }
        self._merge_persistence_candidates(
            state,
            memory_candidates=parsed.get("memory_candidates"),
            event_candidates=parsed.get("event_candidates"),
        )
        parsed["action_status"] = action_status
        parsed["action_type"] = action_type
        parsed["public_message"] = public_message
        parsed["internal_analysis"] = internal_analysis
        parsed["plan_payload"] = copy.deepcopy(plan_payload)
        parsed["operation_result"] = operation_result
        result = self._record_specialist_result(
            state,
            "training_specialist",
            parsed,
            domain_status,
            plan_signal,
            pending_action,
        )
        self._append_coach_handoff(state, "training_specialist", "TREINO", result)
        state.node_outputs["training_specialist"] = internal_analysis

    @staticmethod
    def _has_material_plan_summary(text: str) -> bool:
        if not text or not text.strip():
            return False
        if len(text.strip()) < 30:
            return False
        text_lower = text.lower()
        has_decision = any(
            token in text_lower
            for token in [
                "plan decision", "decisão", "created", "criado",
                "discovery", "descoberta", "persisted", "persistido",
                "specialist", "especialista",
            ]
        )
        has_blockers = any(
            token in text_lower
            for token in ["blocker", "bloqueador", "next action", "próximo"]
        )
        return has_decision or has_blockers

    @staticmethod
    def _is_nutrition_plan_context(state: GraphState) -> bool:
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
    def _has_material_nutrition_summary(text: str) -> bool:
        if not text or not text.strip():
            return False
        text_lower = text.lower()
        has_objective = "nutrition objective" in text_lower or "objetivo nutricional" in text_lower
        has_context = "context used" in text_lower or "contexto usado" in text_lower
        has_rationale = "decision rationale" in text_lower or "racional" in text_lower
        has_fit = "why this fits" in text_lower or "por que isso serve" in text_lower
        has_target_strategy = "target strategy" in text_lower or "estratégia de metas" in text_lower
        has_adherence = "adherence strategy" in text_lower or "estratégia de aderência" in text_lower
        return (
            has_objective
            and has_context
            and has_rationale
            and has_fit
            and has_target_strategy
            and has_adherence
        )

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
        domain_status = str(parsed.get("domain_status", "generated")).strip() or "generated"
        plan_signal = str(parsed.get("plan_signal", "")).strip()
        action_status = str(parsed.get("action_status", "no_action_needed")).strip()
        action_type = str(parsed.get("action_type", "analyze")).strip()
        public_message = str(parsed.get("public_message", "")).strip()
        internal_analysis = str(
            parsed.get(
                "internal_analysis",
                parsed.get("technical_summary", parsed.get("analysis_text", "")),
            )
        ).strip()
        operation_result = self._normalize_operation_result(parsed.get("operation_result"))
        missing_inputs = parsed.get("missing_inputs", [])
        if not isinstance(missing_inputs, list):
            missing_inputs = []
        pending_action = self._normalize_pending_action(parsed.get("pending_action"))
        invalid_specialist_owned_question = (
            action_status == ActionStatus.NEEDS_USER_INPUT.value
            and self._are_only_specialist_owned_slots(
                "nutrition",
                pending_action.get("missing_slots", missing_inputs) or missing_inputs,
            )
        )
        if (
            action_status == "executed"
            and operation_result["attempted"]
            and not operation_result["succeeded"]
        ):
            action_status = "failed"
            public_message = public_message or (
                "Nao consegui ajustar ou salvar a informacao nutricional solicitada."
            )
        if invalid_specialist_owned_question:
            action_status = ActionStatus.FAILED.value
            domain_status = "specialist_role_violation"
            plan_signal = plan_signal or "specialist_role_violation"
            public_message = ""
            internal_analysis = (
                "Nutrition specialist requested specialist-owned technical parameters from "
                "the user. This violates decision ownership."
            )
            missing_inputs = []
            pending_action = {
                "kind": "none",
                "status": "no_action_needed",
                "missing_slots": [],
            }
        is_plan_context = self._is_nutrition_plan_context(state)
        plan_text = internal_analysis
        if (
            is_plan_context
            and domain_status != "specialist_role_violation"
            and not self._has_material_nutrition_summary(internal_analysis)
        ):
            if not plan_signal:
                plan_signal = "insufficient_nutrition_detail"
            domain_status = "insufficient_detail"
            plan_text = ""
            internal_analysis = ""
            if action_status != "no_action_needed":
                public_message = public_message or (
                    "A contribuicao de nutricao ainda esta insuficiente para criar ou revisar o plano com seguranca."
                )
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
        parsed["action_status"] = action_status
        parsed["action_type"] = action_type
        parsed["public_message"] = public_message
        parsed["internal_analysis"] = internal_analysis
        parsed["operation_result"] = operation_result
        result = self._record_specialist_result(
            state,
            "nutrition_specialist",
            parsed,
            domain_status,
            plan_signal,
            pending_action,
        )
        self._append_coach_handoff(state, "nutrition_specialist", "NUTRICAO", result)
        state.node_outputs["nutrition_specialist"] = internal_analysis

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
        public_message = str(parsed.get("public_message", "")).strip()
        internal_analysis = str(
            parsed.get("internal_analysis", parsed.get("technical_summary", ""))
        ).strip()
        operation_result = self._normalize_operation_result(parsed.get("operation_result"))
        tool_operation_result = self._operation_result_from_tool_results(
            state,
            "plan_specialist",
            "upsert_plan",
        )
        if tool_operation_result is not None and (
            not tool_operation_result["succeeded"]
            or not operation_result["attempted"]
        ):
            operation_result = tool_operation_result
        action_status = str(parsed.get("action_status", "no_action_needed")).strip()
        pending_slots = parsed.get("pending_slots", [])
        if not isinstance(pending_slots, list):
            pending_slots = []
        resolved_slots = parsed.get("resolved_slots", [])
        if not isinstance(resolved_slots, list):
            resolved_slots = []
        pending_action = self._normalize_pending_action(parsed.get("pending_action"))
        if (
            plan_status in ("active", "created", "updated")
            and action_status == "executed"
            and not operation_result.get("succeeded")
        ):
            plan_status = "update_failed"
            action_status = "failed"
            public_message = public_message or (
                "Nao consegui salvar a atualizacao do plano."
            )
        if str(operation_result.get("error_code", "")).startswith("ERRO_UPSERT_PLAN_"):
            plan_status = "update_failed"
            action_status = "failed"
            pending_action = {
                "kind": "plan_review",
                "status": "needs_user_input",
                "missing_slots": pending_action.get("missing_slots", []),
            }
        is_claiming_success = (
            plan_status in ("active", "created", "updated")
            and action_status == "executed"
        )
        if is_claiming_success and not self._has_material_plan_summary(internal_analysis):
            plan_status = "discovery_needed"
            action_status = "needs_user_input"
            internal_analysis = (
                "Plano reivindicou conclusao mas a analise interna e insuficiente. "
                "Discovery necessario."
            )
            public_message = public_message or (
                "Ainda falta informacao para concluir a atualizacao do plano com seguranca."
            )
        training_analysis = state.shared_context.get("training_analysis", {})
        nutrition_analysis = state.shared_context.get("nutrition_analysis", {})
        training_status = str(training_analysis.get("status", "")).strip()
        nutrition_status = str(nutrition_analysis.get("status", "")).strip()
        training_role_violation = training_status == "specialist_role_violation"
        nutrition_role_violation = nutrition_status == "specialist_role_violation"
        training_material = training_status not in ("", "no_action_needed", "insufficient_detail")
        nutrition_material = nutrition_status not in ("", "no_action_needed", "insufficient_detail")
        plan_signal = "plan_update"
        combined_text = " ".join(
            [
                str(training_analysis.get("plan_signal", "")),
                str(nutrition_analysis.get("plan_signal", "")),
                reason,
                internal_analysis,
                plan_candidate,
            ]
        ).lower()
        full_plan_creation = plan_status in ("active", "created") and "creation" in combined_text
        training_only_update = (
            plan_status in ("active", "updated")
            and ("training" in combined_text or "treino" in combined_text)
            and not ("nutrition" in combined_text or "nutri" in combined_text)
        )
        nutrition_only_update = (
            plan_status in ("active", "updated")
            and ("nutrition" in combined_text or "nutri" in combined_text)
            and not ("training" in combined_text or "treino" in combined_text)
        )
        if training_role_violation or nutrition_role_violation:
            plan_status = "update_failed"
            action_status = "failed"
            pending_slots = []
            pending_action = {
                "kind": "none",
                "status": "no_action_needed",
                "missing_slots": [],
            }
            public_message = ""
            internal_analysis = (
                "A specialist delegated a specialist-owned technical decision back to the user. "
                "The runtime rejected that pending action."
            )
        elif full_plan_creation and (not training_material or not nutrition_material):
            plan_status = "discovery_needed"
            action_status = "needs_user_input"
            public_message = public_message or (
                "Ainda preciso de contribuicoes materiais de treino e nutricao para criar o plano."
            )
        elif training_only_update and not training_material:
            plan_status = "discovery_needed"
            action_status = "needs_user_input"
            public_message = public_message or (
                "Ainda preciso de uma analise material de treino para atualizar essa parte do plano."
            )
        elif nutrition_only_update and not nutrition_material:
            plan_status = "discovery_needed"
            action_status = "needs_user_input"
            public_message = public_message or (
                "Ainda preciso de uma analise material de nutricao para atualizar essa parte do plano."
            )
        self._merge_persistence_candidates(
            state,
            memory_candidates=parsed.get("memory_candidates"),
            event_candidates=parsed.get("event_candidates"),
        )
        state.node_outputs["plan_specialist"] = internal_analysis or (
            "Objetivo: gerenciar ciclo de vida do plano e consistencia entre treino e nutricao. "
            f"has_active_plan={state.shared_context['has_active_plan']}; "
            f"plan_status={plan_status}; revisao_necessaria={state.plan_needs_revision}; reason={reason}"
        )
        state.shared_context["plan_workspace"] = {
            "active_domain": active_domain,
            "has_active_plan": state.shared_context["has_active_plan"],
            "plan_status": plan_status,
            "needs_revision": state.plan_needs_revision,
            "reason": reason,
            "plan_candidate": plan_candidate,
            "operation_result": operation_result,
            "public_message": public_message,
            "internal_analysis": internal_analysis,
            "lifecycle": state.shared_context.get("plan_lifecycle", {}),
            "training_preview": self._truncate(
                state.node_outputs.get("training_specialist", ""), 280
            ),
            "nutrition_preview": self._truncate(
                state.node_outputs.get("nutrition_specialist", ""), 280
            ),
        }
        parsed["action_status"] = action_status
        parsed["action_type"] = plan_status or "plan"
        parsed["public_message"] = public_message
        parsed["internal_analysis"] = internal_analysis
        parsed["operation_result"] = operation_result
        parsed["missing_inputs"] = pending_slots
        result = self._record_specialist_result(
            state,
            "plan_specialist",
            parsed,
            plan_status,
            plan_signal,
            pending_action,
        )
        state.specialist_states["plan_specialist"]["pending_slots"] = pending_slots
        self._append_coach_handoff(state, "plan_specialist", "PLANO", result)

    async def _node_coach_reply(self, state: GraphState) -> None:
        if state.security_status != "safe":
            state.coach_response = self._blocked_response()
            state.node_outputs["coach_reply"] = state.coach_response
            return

        sanitized_handoff = [
            item
            for item in state.coach_handoff
            if not (
                item.get("action_status") == ActionStatus.FAILED.value
                and not str(item.get("public_message", "")).strip()
            )
        ]

        handoff_payload: dict[str, Any] = {
            "coach_handoff": sanitized_handoff,
            "rules": {
                "use_only_public_message": True,
                "do_not_add_success_claims": True,
                "failed_operations_must_remain_failed": True,
            },
        }
        if not sanitized_handoff:
            handoff_payload = {"coach_handoff": [], "no_specialist_action": True}
        specialist_context = json.dumps(
            handoff_payload,
            ensure_ascii=True,
            sort_keys=True,
        )

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
        if self._has_failed_material_operation(state):
            state.node_outputs["memory_hub"] = "blocked_failed_operation"
            self._log_persistence_decision(state, "blocked_failed_operation")
            return
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
                "SPECIALIST_RESULTS_JSON:\n"
                f"{json.dumps(state.specialist_results, ensure_ascii=True, sort_keys=True)}\n\n"
                "PERSISTENCE_CANDIDATES_JSON:\n"
                f"{json.dumps(state.shared_context.get('persistence_candidates', {}), ensure_ascii=True, sort_keys=True)}"
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
                metadata = state.node_metadata.setdefault(node_name, {})
                metadata.setdefault("tools_called", []).append(tool_name)
                metadata.setdefault("tool_results", []).append(
                    {
                        "tool_name": tool_name,
                        "status": str(chunk.get("status", "")).strip(),
                        "content": self._truncate(
                            str(chunk.get("content", chunk.get("result", ""))),
                            4000,
                        ),
                    }
                )
        raw_response = "".join(chunks).strip() or state.user_input_sanitized
        state.last_raw_outputs[node_name] = raw_response
        return raw_response

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
            "specialist_results": json.dumps(
                state.specialist_results, ensure_ascii=True, sort_keys=True
            ),
            "coach_handoff": json.dumps(
                state.coach_handoff, ensure_ascii=True, sort_keys=True
            ),
            "coach_response": str(state.coach_response),
            "security_result": str(state.security_status),
            "persistence_intents": str(state.persistence_intents),
            "persistence_candidates": json.dumps(
                state.shared_context.get("persistence_candidates", {}),
                ensure_ascii=True,
                sort_keys=True,
            ),
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
        plan_workspace = state.shared_context.get("plan_workspace", {})
        payload = (
            f"RUNTIME_CONTEXT_JSON:\n{self._truncate(runtime_json, 4000)}\n\n"
            f"PLAN_SECTION:\n{self._truncate(plan_section, 1200)}\n\n"
            f"AGENDA_SECTION:\n{self._truncate(agenda_section, 1200)}\n\n"
            f"METABOLISM_SECTION:\n{self._truncate(metabolism_section, 1200)}\n\n"
            f"PLAN_LIFECYCLE:\n{state.shared_context.get('plan_lifecycle', {})}\n\n"
            f"PLAN_WORKSPACE:\nplan_status={plan_workspace.get('plan_status', '')} "
            f"needs_revision={plan_workspace.get('needs_revision', False)} "
            f"reason={plan_workspace.get('reason', '')}"
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
