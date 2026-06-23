"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""
# pylint: disable=too-many-lines

import asyncio
import json
import re
import unicodedata
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks, HTTPException
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from src.core.config import settings
from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.prompt_builder import PromptBuilder
from src.utils.date_utils import parse_cycle_start
from src.services.workout_tools import (
    create_save_workout_tool,
    create_get_workouts_tool,
)
from src.services.nutrition_tools import (
    create_save_nutrition_tool,
    create_get_nutrition_tool,
    create_sync_nutrition_text_tool,
)
from src.services.composition_tools import (
    create_save_composition_tool,
    create_get_composition_tool,
)
from src.services.metabolism_tools import (
    create_get_metabolism_tool,
    create_update_tdee_params_tool,
    create_reset_tdee_tracking_tool,
)
from src.services.memory_tools import (
    create_save_memory_tool,
    create_search_memory_tool,
    create_list_raw_memories_tool,
    create_update_memory_tool,
    create_delete_memory_tool,
    create_delete_memories_batch_tool,
)
from src.services.event_tools import (
    create_create_event_tool,
    create_list_events_tool,
    create_delete_event_tool,
    create_update_event_tool,
)
from src.services.hevy_tools import (
    create_list_hevy_routines_tool,
    create_create_hevy_routine_tool,
    create_update_hevy_routine_tool,
    create_search_hevy_exercises_tool,
    create_replace_hevy_exercise_tool,
    create_get_hevy_routine_detail_tool,
    create_set_routine_rest_and_ranges_tool,
    create_trigger_hevy_import_tool,
)
from src.services.hevy_service import HevyService
from src.utils.qdrant_utils import point_to_dict
from src.services.raw_data_tools import (
    create_get_workouts_raw_tool,
    create_get_nutrition_raw_tool,
    create_get_body_composition_raw_tool,
    create_get_events_raw_tool,
    create_get_memories_raw_tool,
)
from src.services.plan_tools import (
    create_create_plan_from_discovery_tool,
    create_get_plan_status_tool,
    create_plan_help_tool,
    create_get_plan_tool,
    create_record_plan_review_tool,
    create_update_plan_discovery_tool,
    create_update_plan_section_tool,
)
from src.services.plan_training_tools import (
    create_get_plan_training_program_tool,
)
from src.services.memory_service import (
    get_memories_paginated as paginate_memories,
    add_memory as service_add_memory,
)
from src.services.plan_service import build_plan_prompt_snapshot, build_progress_snapshot
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.repositories.event_repository import EventRepository
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.workout_log import WorkoutLog

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


class AITrainerBrain:  # pylint: disable=too-many-public-methods,too-many-instance-attributes
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """
    _MSG_OPEN_PATTERN = re.compile(r'<msg(?:\s+data="[^"]*")?(?:\s+hora="[^"]*")?>')
    _TREINADOR_OPEN_PATTERN = re.compile(r'<treinador(?:\s+name="[^"]*")?>')
    _FINAL_REPLY_HISTORY_MESSAGES = 6
    _EXPLICIT_PLAN_APPROVAL_MESSAGES = {
        "ok",
        "meu ok",
        "pode atualizar",
        "pode aplicar",
        "pode mudar",
        "manda ver",
        "pode fazer",
        "sinal verde",
    }
    _PLAN_UPDATE_CONTEXT_HINTS = (
        "atualizar o plano",
        "ajustar o plano",
        "alterar o plano",
        "mudar o plano",
        "aplicar no plano",
        "aplicar essa mudanca",
        "plano ativo",
        "posso atualizar",
        "posso aplicar",
        "sinal verde",
    )
    _PLAN_CREATE_CONTEXT_HINTS = (
        "criar o plano",
        "montar o plano",
        "gerar o plano",
        "fechar o plano",
        "ja tenho tudo para criar o plano",
        "posso criar",
        "pode criar",
    )
    _RECONFIRMATION_HINTS = (
        "me confirma",
        "me de o sinal verde",
        "me da o sinal verde",
        "posso atualizar",
        "posso aplicar",
        "quer que eu aplique",
        "quer que eu atualize",
        "esta 100 pronto",
        "so confirmar",
    )

    def __init__(
        self,
        database: MongoDatabase,
        llm_client: LLMClient,
        qdrant_client: Optional["QdrantClient"] = None,
    ):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._qdrant_client = qdrant_client
        self.prompt_builder = PromptBuilder()
        self._executor = ThreadPoolExecutor(
            max_workers=settings.AI_TRAINER_THREADPOOL_WORKERS
        )

    def calculate_effective_limits(
        self, profile: UserProfile, plan
    ) -> tuple[int | None, int | None]:
        """Calculates effective limits applying overrides."""
        daily = plan.daily_limit
        monthly = plan.monthly_limit
        if profile.custom_message_limit is not None:
            if plan.daily_limit is not None:
                daily = profile.custom_message_limit
            elif plan.monthly_limit is not None:
                monthly = profile.custom_message_limit
        return daily, monthly

    def check_message_limits(self, profile: UserProfile) -> bool:
        """
        Verifies if the user has reached their message limit.
        """
        try:
            plan_name = SubscriptionPlan(profile.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE

        plan = SUBSCRIPTION_PLANS[plan_name]
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        needs_reset, cycle_start = self.check_billing_cycle(profile, now)

        # 1. Trial
        validity = (
            profile.custom_trial_days
            if profile.custom_trial_days is not None
            else plan.validity_days
        )
        if validity is not None and cycle_start:
            # Ensure cycle_start is aware
            if cycle_start.tzinfo is None:
                cycle_start = cycle_start.replace(tzinfo=timezone.utc)

            if now - cycle_start >= timedelta(days=validity):
                raise HTTPException(status_code=403, detail="TRIAL_EXPIRED")

        # 2. Limits
        eff_daily, eff_monthly = self.calculate_effective_limits(profile, plan)

        if eff_daily is not None:
            count = (
                profile.messages_sent_today
                if profile.last_message_date == today_str
                else 0
            )
            if count >= eff_daily:
                raise HTTPException(status_code=403, detail="DAILY_LIMIT_REACHED")

        if eff_monthly is not None:
            count = (
                0 if needs_reset else getattr(profile, "messages_sent_this_month", 0)
            )
            if count >= eff_monthly:
                raise HTTPException(status_code=403, detail="LIMITE_MENSAGENS_MES")

        return needs_reset

    def check_billing_cycle(
        self, profile: UserProfile, now: datetime
    ) -> tuple[bool, datetime | None]:
        """Checks if the billing cycle needs reset."""
        if profile.current_billing_cycle_start is None:
            return True, None

        cycle_start = parse_cycle_start(profile.current_billing_cycle_start, now)

        needs_reset = now - cycle_start >= timedelta(days=30)
        return needs_reset, cycle_start

    def increment_counts(self, user_email: str, needs_cycle_reset: bool):
        """
        Background task to increment message counts.
        """
        new_cycle_start = datetime.now(timezone.utc) if needs_cycle_reset else None
        self._database.increment_user_message_counts(user_email, new_cycle_start)

    @property
    def database(self) -> MongoDatabase:
        """Returns the database instance."""
        return self._database

    def log_prompt_in_background(
        self,
        user_email: str,
        prompt_data: dict,
        background_tasks: Optional[BackgroundTasks] = None,
    ):
        """
        Helper to log prompts to DB in background if tasks available, or sync if not.
        """
        if background_tasks:
            background_tasks.add_task(
                self._database.log_prompt, user_email, prompt_data
            )
        else:
            try:
                # Fallback for sync callers or when BackgroundTasks not provided
                self._database.log_prompt(user_email, prompt_data)
            except (ValueError, TypeError, AttributeError) as e:
                logger.error("Error logging prompt to DB: %s", e)

    def get_log_callback(self, background_tasks: Optional[BackgroundTasks] = None):
        """
        Returns a callback for LLMClient to use for logging.
        """

        def callback(email: str, data: dict):
            self.log_prompt_in_background(email, data, background_tasks)

        return callback

    def get_chat_history(
        self, session_id: str, limit: int = 20, offset: int = 0
    ) -> list[ChatHistory]:
        """
        Retrieves the chat history for a given session ID.

        Args:
            session_id (str): The session ID.
            limit (int): Number of messages to retrieve.
            offset (int): Number of messages to skip from the end (most recent).

        Returns:
            list[ChatHistory]: A list of chat messages.
        """
        logger.debug(
            "Attempting to retrieve chat history for session: %s (limit: %d, offset: %d)",
            session_id,
            limit,
            offset,
        )
        messages = self._database.get_chat_history(session_id, limit, offset)
        for message in messages:
            if message.sender == Sender.TRAINER:
                message.text = self.normalize_public_chat_text(message.text)
                if message.translations:
                    message.translations = {
                        locale: self.normalize_public_chat_text(value)
                        for locale, value in message.translations.items()
                    }
        return messages

    def get_user_profile(self, email: str) -> UserProfile | None:
        """
        Retrieves a user profile from the database.
        """
        return self._database.get_user_profile(email)

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """
        Retrieves a trainer profile from the database.
        """
        return self._database.get_trainer_profile(email)

    def save_user_profile(self, profile: UserProfile):
        """
        Saves a user profile to the database.
        """
        self._database.save_user_profile(profile)

    def update_workout_log(self, workout_id: str, user_email: str, workout: WorkoutLog) -> bool:
        """
        Updates an existing workout log.
        """
        return self._database.update_workout_log(workout_id, user_email, workout)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        """
        Partially updates specific fields in user profile without overwriting others.
        Use this instead of save_user_profile when only updating a subset of fields
        to avoid race conditions with concurrent full-profile updates.
        """
        return self._database.update_user_profile_fields(email, fields)

    def save_trainer_profile(self, profile: TrainerProfile):
        """
        Saves a trainer profile to the database.
        """
        self._database.save_trainer_profile(profile)

    def get_or_create_user_profile(self, user_email: str) -> UserProfile:
        """Retrieves user profile or creates a default one if not found."""
        profile = self.get_user_profile(user_email)
        if not profile:
            logger.info(
                "User profile not found, creating default for user: %s", user_email
            )
            profile = UserProfile(
                email=user_email,
                password_hash=None,
                role="user",
                gender="Masculino",
                age=30,
                weight=None,
                height=175,
                goal="Melhorar condicionamento",
                goal_type="maintain",
                # Mandatory fields for Mypy/Pyright
                target_weight=None,
                weekly_rate=0.0,
                notes=None,
            )
            self.save_user_profile(profile)
        return profile

    def ensure_trainer_allowed(
        self,
        user_email: str,
        plan_name: str,
        trainer_profile: TrainerProfile | None = None,
    ) -> str | None:
        """
        Ensures the current trainer is allowed for the user's plan.
        Returns the new trainer_type if it was changed, otherwise None.
        """
        if not trainer_profile:
            trainer_profile = self.get_trainer_profile(user_email)

        if not trainer_profile:
            return None

        try:
            plan = SubscriptionPlan(plan_name)
        except (ValueError, AttributeError):
            plan = SubscriptionPlan.FREE

        plan_details = SUBSCRIPTION_PLANS[plan]
        allowed = plan_details.allowed_trainers

        if allowed and trainer_profile.trainer_type not in allowed:
            # Reset to the first allowed trainer (usually gymbro/Breno)
            new_trainer = allowed[0]
            logger.info(
                "Trainer %s not allowed for plan %s. Resetting user %s to %s",
                trainer_profile.trainer_type,
                plan_name,
                user_email,
                new_trainer,
            )
            trainer_profile.trainer_type = new_trainer
            self.save_trainer_profile(trainer_profile)
            return new_trainer

        return None

    def get_or_create_trainer_profile(
        self, user_email: str, user_profile: UserProfile | None = None
    ) -> TrainerProfile:
        """Retrieves trainer profile or creates a default one if not found."""
        # 1. Get plan name
        if not user_profile:
            user_profile = self.get_user_profile(user_email)
        plan_name = user_profile.subscription_plan if user_profile else "Free"

        # 2. Get trainer profile
        trainer_profile_obj = self._database.get_trainer_profile(user_email)

        if not trainer_profile_obj:
            logger.info(
                "Trainer profile not found, creating default for user: %s", user_email
            )
            # Default for Free is gymbro, others is atlas
            default_trainer = "gymbro" if plan_name == "Free" else "atlas"
            trainer_profile_obj = TrainerProfile(
                user_email=user_email, trainer_type=default_trainer
            )
            self.save_trainer_profile(trainer_profile_obj)
        else:
            # 3. Ensure allowed for current plan
            self.ensure_trainer_allowed(user_email, plan_name, trainer_profile_obj)

        return trainer_profile_obj

    def add_to_mongo_history(
        self,
        user_email: str,
        user_input: str,
        response_text: str,
        metadata: dict | None = None,
    ):
        """
        Adds the user input and AI response to MongoDB chat history (synchronous).

        Args:
            user_email (str): The user's email.
            user_input (str): The user's input message.
            response_text (str): The AI's response message.
            trainer_type (str): The active trainer profile type.
        """
        now = datetime.now().isoformat()
        metadata = metadata or {}
        trainer_type = metadata.get("trainer_type", "atlas")
        user_images = metadata.get("user_images")
        user_message = ChatHistory(
            sender=Sender.STUDENT,
            text=user_input,
            images=user_images,
            timestamp=now,
            trainer_type=trainer_type,
        )
        ai_message = ChatHistory(
            sender=Sender.TRAINER,
            text=response_text,
            timestamp=now,
            trainer_type=trainer_type,
        )

        # Save to MongoDB (Session History) - synchronous
        self._database.add_many_to_history(
            [user_message, ai_message], user_email, trainer_type
        )
        logger.info(
            "Successfully saved conversation to MongoDB for user: %s (trainer: %s)",
            user_email,
            trainer_type,
        )

    def add_system_message_to_history(self, user_email: str, content: str):
        """
        Adds a SYSTEM message to history (e.g. tool feedback).
        """
        now = datetime.now().isoformat()
        # System messages don't need trainer_type
        system_msg = ChatHistory(sender=Sender.SYSTEM, text=content, timestamp=now)
        self._database.add_to_history(system_msg, user_email)
        logger.debug("Saved SYSTEM message to history: %s", content)

    def sort_messages_by_timestamp(self, messages: list) -> list:
        """
        Sorts LangChain messages by their timestamp in ascending order (oldest first).
        Messages without timestamps are placed at the end.

        Args:
            messages: List of LangChain BaseMessage objects.

        Returns:
            Sorted list of messages.
        """

        def get_timestamp(msg) -> str:
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                return msg.additional_kwargs.get("timestamp", "9999-99-99T99:99:99")
            return "9999-99-99T99:99:99"  # Messages without timestamp go to end

        return sorted(messages, key=get_timestamp)

    def _build_msg_tags(self, msg: BaseMessage) -> tuple[str, str]:
        """Builds XML tags for a message based on its timestamp."""
        if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            ts = msg.additional_kwargs.get("timestamp", "")
            if ts:
                try:
                    dt = datetime.fromisoformat(ts)
                    return (
                        f'<msg data="{dt.strftime("%d/%m")}" hora="{dt.strftime("%H:%M")}">',
                        "</msg>",
                    )
                except (ValueError, TypeError):
                    pass
        return "<msg>", "</msg>"

    def format_history_as_messages(
        self,
        messages: list,
    ) -> list[BaseMessage]:
        """
        Formats LangChain messages into a list of BaseMessage objects for the prompt.
        Preserves the structural integrity of the history (Message objects) without
        adding prefixes, as LangChain already differentiates message types correctly.
        """
        if not messages:
            return []

        # Sort messages chronologically
        messages = self.sort_messages_by_timestamp(messages)

        formatted_msgs: list[BaseMessage] = []
        for msg in messages:
            # Check message type
            if hasattr(msg, "type") and msg.type == "system":
                continue

            # Extract tags and clean content
            prefix, suffix = self._build_msg_tags(msg)
            raw_content = msg.content if msg.content else ""
            content_clean = " ".join(str(raw_content).split())

            if isinstance(msg, HumanMessage):
                formatted_msgs.append(HumanMessage(content=f"{prefix}{content_clean}{suffix}"))

            elif isinstance(msg, AIMessage):
                trainer_name = "Treinador"
                if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                    t_type = msg.additional_kwargs.get("trainer_type", "")
                    if t_type:
                        trainer_name = t_type.capitalize()

                full_content = (
                    f'{prefix}<treinador name="{trainer_name}">'
                    f"{content_clean}</treinador>{suffix}"
                )
                formatted_msgs.append(
                    AIMessage(
                        content=full_content, additional_kwargs=msg.additional_kwargs
                    )
                )
            else:
                formatted_msgs.append(HumanMessage(content=f"{prefix}{content_clean}{suffix}"))

        return formatted_msgs

    @classmethod
    def strip_internal_wrappers(cls, text: str) -> str:
        """
        Remove only internal wrapper tags used by the prompt protocol.
        Keeps all other tags/content intact.
        """
        if not text:
            return ""

        cleaned = cls._MSG_OPEN_PATTERN.sub("", text)
        cleaned = cleaned.replace("</msg>", "")
        cleaned = cls._TREINADOR_OPEN_PATTERN.sub("", cleaned)
        cleaned = cleaned.replace("</treinador>", "")
        return cleaned

    @staticmethod
    def normalize_text_for_intent(text: str) -> str:
        """Normalize free text for deterministic intent checks."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.lower()
        ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
        return re.sub(r"\s+", " ", ascii_text).strip()

    @classmethod
    def _history_to_plain_text(cls, recent_history: list[BaseMessage]) -> str:
        parts: list[str] = []
        for message in recent_history:
            content = str(getattr(message, "content", "") or "")
            cleaned = cls.strip_internal_wrappers(content).strip()
            if cleaned:
                parts.append(cleaned)
        return "\n".join(parts)

    @classmethod
    def _is_explicit_approval_message(cls, normalized_input: str) -> bool:
        if not normalized_input:
            return False
        if normalized_input in cls._EXPLICIT_PLAN_APPROVAL_MESSAGES:
            return True
        return any(
            phrase in normalized_input
            for phrase in cls._EXPLICIT_PLAN_APPROVAL_MESSAGES
            if " " in phrase
        )

    @classmethod
    def _has_plan_update_context(cls, normalized_history: str) -> bool:
        if not normalized_history:
            return False
        if any(hint in normalized_history for hint in cls._PLAN_UPDATE_CONTEXT_HINTS):
            return True
        has_plan = "plano" in normalized_history
        has_mutation = any(
            token in normalized_history
            for token in ("atualiz", "ajust", "alter", "mudar", "aplic")
        )
        return has_plan and has_mutation

    @classmethod
    def _has_plan_create_context(cls, normalized_history: str) -> bool:
        if not normalized_history:
            return False
        if any(hint in normalized_history for hint in cls._PLAN_CREATE_CONTEXT_HINTS):
            return True
        return "plano" in normalized_history and any(
            token in normalized_history
            for token in ("criar", "montar", "gerar", "fechar")
        )

    @classmethod
    def detect_explicit_plan_execution(
        cls,
        *,
        user_input: str,
        recent_history: list[BaseMessage],
        plan_snapshot,
    ) -> dict | None:
        """Detect explicit approval that should force immediate plan execution."""
        normalized_input = cls.normalize_text_for_intent(user_input)
        if not cls._is_explicit_approval_message(normalized_input):
            return None

        normalized_history = cls.normalize_text_for_intent(
            cls._history_to_plain_text(recent_history[-cls._FINAL_REPLY_HISTORY_MESSAGES :])
        )
        if getattr(plan_snapshot, "status", None) == "ACTIVE_PLAN":
            if not cls._has_plan_update_context(normalized_history):
                return None
            return {
                "mode": "update_active_plan",
                "required_tool": "update_plan_section",
            }

        discovery = getattr(plan_snapshot, "discovery", {}) or {}
        missing_fields = discovery.get("missing_fields") or []
        if missing_fields:
            return None
        if not cls._has_plan_create_context(normalized_history):
            return None
        return {
            "mode": "create_from_discovery",
            "required_tool": "create_plan_from_discovery",
        }

    @classmethod
    def apply_explicit_plan_execution_context(
        cls,
        input_data: dict,
        approval_context: dict,
    ) -> dict:
        """Inject deterministic execution flags into prompt runtime context."""
        runtime_context = dict(input_data.get("runtime_context") or {})
        runtime_context["plan_execution"] = {
            "explicit_user_approval": True,
            "mode": approval_context["mode"],
            "required_tool": approval_context["required_tool"],
            "must_execute_now": True,
        }
        input_data["runtime_context"] = runtime_context
        input_data["runtime_context_json"] = json.dumps(
            runtime_context, ensure_ascii=True, sort_keys=True
        )
        input_data["explicit_plan_approval"] = True
        input_data["plan_execution_mode"] = approval_context["mode"]
        input_data["required_plan_tool"] = approval_context["required_tool"]
        return input_data

    @classmethod
    def normalize_public_chat_text(cls, text: str) -> str:
        """
        Normalize persisted chat text before sending it to clients.
        This covers older production payload variants that break markdown tables.
        """
        if not text:
            return ""

        normalized = cls.strip_internal_wrappers(text)
        normalized = (
            normalized.replace("\\u007c", "|")
            .replace("\\U007C", "|")
            .replace("&#124;", "|")
            .replace("&#x7C;", "|")
            .replace("｜", "|")
            .replace("│", "|")
            .replace("\\r\\n", "\n")
            .replace("\\n", "\n")
            .replace("\\r", "\n")
            .replace("\\|", "|")
        )
        normalized = re.sub(r"[\u200B-\u200D\uFEFF]", "", normalized)

        if re.search(r"\|\s*:?-{3,}\s*\|", normalized):
            normalized = re.sub(r"\|\s*\|", "|\n|", normalized)

        return normalized

    @classmethod
    def split_stream_visible_text(cls, buffer: str) -> tuple[str, str]:
        """
        Split a stream buffer into visible text and an optional partial tag tail.
        Only handles the internal wrapper tags (<msg>, <treinador>).
        """
        if not buffer:
            return "", ""

        last_lt = buffer.rfind("<")
        last_gt = buffer.rfind(">")
        has_partial_tag = last_lt > last_gt

        stable = buffer[:last_lt] if has_partial_tag else buffer
        pending = buffer[last_lt:] if has_partial_tag else ""
        return cls.strip_internal_wrappers(stable), pending

    @classmethod
    def enforce_plan_update_truth_policy(
        cls,
        *,
        final_response: str,
        tool_events: list[dict],
        user_locale: str | None,
    ) -> str:
        """Prevent false success claims when no material plan change was saved."""
        attempted_update = any(
            event.get("tool_name") in {"update_plan_section", "create_plan_from_discovery"}
            for event in tool_events
        )
        if not attempted_update:
            return final_response

        material_change = False
        for event in tool_events:
            content = event.get("content")
            if not isinstance(content, str):
                continue
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                continue
            if payload.get("plan_materially_changed") is True:
                material_change = True
                break

        if material_change:
            return final_response

        if user_locale == "en-US":
            return (
                "I could not apply a material update to your plan. "
                "The update attempts were blocked by consistency checks, "
                "so your active plan remains unchanged."
            )
        if user_locale == "es-ES":
            return (
                "No pude aplicar una actualización material a tu plan. "
                "Los intentos de actualización fueron bloqueados por validaciones "
                "de consistencia, por lo que tu plan activo sigue sin cambios."
            )
        return (
            "Nao consegui aplicar uma atualizacao material no seu plano. "
            "As tentativas de update foram bloqueadas por validacoes de consistencia, "
            "entao o plano ativo continua sem mudanca."
        )

    @staticmethod
    def format_sse_event(event: str, payload: dict | str) -> str:
        """Serialize one SSE event frame."""
        data = (
            payload
            if isinstance(payload, str)
            else json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
        )
        return f"event: {event}\ndata: {data}\n\n"

    @classmethod
    def summarize_tool_events(cls, tool_events: list[dict]) -> dict:
        """Extract factual tool outcome summary for the final response round."""
        results: list[dict] = []
        material_plan_change = False
        any_saved = False
        any_failure = False

        for event in tool_events:
            content = event.get("content")
            if not isinstance(content, str):
                continue
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                payload = {"raw_content": content}

            result = {
                "tool_name": event.get("tool_name"),
                "status": payload.get("status"),
                "saved": bool(payload.get("saved")),
                "plan_materially_changed": bool(
                    payload.get("plan_materially_changed")
                ),
                "changed_sections": payload.get("changed_sections") or [],
                "message_for_ai": payload.get("message_for_ai"),
                "missing_fields": payload.get("missing_fields") or [],
                "validation_errors": payload.get("validation_errors") or [],
                "external_sync_failed": bool(payload.get("external_sync_failed")),
            }
            results.append(result)
            material_plan_change = material_plan_change or result["plan_materially_changed"]
            any_saved = any_saved or result["saved"]
            status = result["status"]
            any_failure = any_failure or (
                status
                not in {
                    None,
                    "success",
                    "review_recorded",
                    "discovery_updated",
                    "ACTIVE_PLAN",
                    "NO_PLAN",
                }
                and not result["saved"]
            )

        return {
            "material_plan_change": material_plan_change,
            "any_saved": any_saved,
            "any_failure": any_failure,
            "attempted_material_plan_write": any(
                result["tool_name"] in {"update_plan_section", "create_plan_from_discovery"}
                for result in results
            ),
            "tool_results": results,
        }

    @classmethod
    def _latest_plan_tool_result(
        cls,
        tool_events: list[dict],
        required_tool: str,
    ) -> dict | None:
        for event in reversed(tool_events):
            if event.get("tool_name") != required_tool:
                continue
            content = event.get("content")
            if not isinstance(content, str):
                continue
            try:
                payload = json.loads(content)
            except json.JSONDecodeError:
                payload = {"message_for_ai": content}
            payload["tool_name"] = required_tool
            return payload
        return None

    @classmethod
    def _contains_reconfirmation_request(cls, text: str) -> bool:
        normalized = cls.normalize_text_for_intent(text)
        return any(hint in normalized for hint in cls._RECONFIRMATION_HINTS)

    @classmethod
    # pylint: disable=too-many-return-statements,too-many-branches
    def _compose_plan_execution_blocker(
        cls,
        *,
        approval_context: dict,
        tool_events: list[dict],
        user_locale: str | None,
    ) -> str:
        required_tool = approval_context["required_tool"]
        latest_result = cls._latest_plan_tool_result(tool_events, required_tool)
        if latest_result is None:
            if user_locale == "en-US":
                return (
                    f"This turn did not execute `{required_tool}` after your explicit approval, "
                    "so no plan change was applied."
                )
            if user_locale == "es-ES":
                return (
                    f"Este turno no ejecutó `{required_tool}` después de tu aprobación explícita, "
                    "así que no se aplicó ningún cambio al plan."
                )
            return (
                f"Este turno nao executou `{required_tool}` depois do seu OK explicito, "
                "entao nenhuma mudanca foi aplicada ao plano."
            )

        status = latest_result.get("status")
        validation_errors = latest_result.get("validation_errors") or []
        first_error = validation_errors[0].get("msg") if validation_errors else None
        message_for_ai = latest_result.get("message_for_ai")
        missing_fields = latest_result.get("missing_fields") or []

        if status == "discovery_needed" and missing_fields:
            missing_label = ", ".join(str(field) for field in missing_fields)
            if user_locale == "en-US":
                return f"Discovery is still incomplete: {missing_label}."
            if user_locale == "es-ES":
                return f"El discovery sigue incompleto: {missing_label}."
            return f"O discovery ainda esta incompleto: {missing_label}."
        if status == "no_plan":
            if user_locale == "en-US":
                return "There is no active plan to update yet."
            if user_locale == "es-ES":
                return "Todavia no existe un plan activo para actualizar."
            return "Ainda nao existe um plano ativo para atualizar."
        if first_error:
            return str(first_error)
        if isinstance(message_for_ai, str) and message_for_ai.strip():
            return message_for_ai.strip()
        if user_locale == "en-US":
            return "The requested plan execution did not persist a material change."
        if user_locale == "es-ES":
            return "La ejecucion solicitada del plan no guardo un cambio material."
        return "A execucao solicitada do plano nao salvou uma mudanca material."

    @classmethod
    # pylint: disable=too-many-return-statements
    def render_explicit_plan_execution_response(
        cls,
        *,
        approval_context: dict,
        tool_events: list[dict],
        user_locale: str | None,
    ) -> str:
        """Build deterministic user-facing output for explicit approval turns."""
        required_tool = approval_context["required_tool"]
        latest_result = cls._latest_plan_tool_result(tool_events, required_tool)
        if latest_result and latest_result.get("saved") and latest_result.get(
            "plan_materially_changed"
        ):
            if approval_context["mode"] == "create_from_discovery":
                if user_locale == "en-US":
                    return "Your plan was created successfully."
                if user_locale == "es-ES":
                    return "Tu plan se creo correctamente."
                return "Plano criado com sucesso."
            if user_locale == "en-US":
                return "Your plan was updated successfully."
            if user_locale == "es-ES":
                return "Tu plan se actualizo correctamente."
            return "Plano atualizado com sucesso."

        blocker = cls._compose_plan_execution_blocker(
            approval_context=approval_context,
            tool_events=tool_events,
            user_locale=user_locale,
        )
        if user_locale == "en-US":
            return f"I did not execute the requested plan change. Blocker: {blocker}"
        if user_locale == "es-ES":
            return f"No ejecute el cambio solicitado del plan. Bloqueo: {blocker}"
        return f"Nao executei a mudanca solicitada no plano. Bloqueio: {blocker}"

    def build_final_response_prompt(self) -> ChatPromptTemplate:
        """Prompt for the final user-facing round with tools disabled."""
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "Voce escreve a resposta final visivel ao usuario. "
                        "Use apenas os fatos do TOOL_OUTCOME_JSON, "
                        "do runtime context e do historico recente. "
                        "Nunca invente sucesso operacional. "
                        "Se EXPLICIT_PLAN_APPROVAL=true, isso significa que o usuario "
                        "ja autorizou a execucao neste turno. "
                        "Nao faca nova pergunta de confirmacao, nao peca sinal verde "
                        "e nao devolva reconfirmacao. "
                        "Se material_plan_change=false, diga claramente "
                        "que o plano ativo nao mudou. "
                        "Se houve erro de validacao ou sincronizacao externa, "
                        "explique de forma curta e objetiva. "
                        "Responda no locale pedido em user_locale."
                    ),
                ),
                (
                    "system",
                    (
                        "user_locale={user_locale}\n"
                        "EXPLICIT_PLAN_APPROVAL={explicit_plan_approval}\n"
                        "PLAN_EXECUTION_MODE={plan_execution_mode}\n"
                        "REQUIRED_PLAN_TOOL={required_plan_tool}\n"
                        "RUNTIME_CONTEXT_JSON:\n{runtime_context_json}\n"
                        "TOOL_OUTCOME_JSON:\n{tool_outcome_json}\n"
                        "ASSISTANT_DRAFT:\n{assistant_draft}"
                    ),
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                (
                    "human",
                    "Ultima mensagem do usuario:\n{user_message}",
                ),
            ]
        )

    def _safe_user_facing_error_message(self, locale: str | None) -> str:
        """Return a JSON-serializable localized error string even under mocks."""
        message = self._llm_client.get_user_facing_error_message(locale)
        if isinstance(message, str):
            return message
        return LLMClient.get_user_facing_error_message(locale)

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    async def build_final_response_input(
        self,
        *,
        user_email: str,
        profile: UserProfile,
        user_input: str,
        runtime_context_json: str,
        user_locale: str,
        tool_summary: dict,
        assistant_draft: str,
        explicit_plan_approval: bool = False,
        plan_execution_mode: str = "none",
        required_plan_tool: str = "none",
    ) -> dict:
        """Create compact prompt input for the final no-tools response round."""
        recent_history = (
            await asyncio.to_thread(
                self._database.get_window_memory(
                    session_id=user_email,
                    k=self._FINAL_REPLY_HISTORY_MESSAGES,
                ).load_memory_variables,
                {},
            )
        ).get("chat_history", [])

        return {
            "chat_history": self.format_history_as_messages(recent_history),
            "user_message": user_input,
            "runtime_context_json": runtime_context_json,
            "tool_outcome_json": json.dumps(tool_summary, ensure_ascii=True, sort_keys=True),
            "assistant_draft": assistant_draft,
            "user_locale": user_locale,
            "explicit_plan_approval": str(explicit_plan_approval).lower(),
            "plan_execution_mode": plan_execution_mode,
            "required_plan_tool": required_plan_tool,
            "user_profile_obj": profile,
        }

    def get_tools(self, user_email: str) -> list[BaseTool]:
        """
        Creates and returns a list of tools available to the AI.
        """
        profile = self._database.get_user_profile(user_email)
        hevy_enabled = bool(profile and profile.hevy_enabled and profile.hevy_api_key)
        hevy_service = HevyService(workout_repository=self._database.workouts_repo)

        tools = [
            # Workout
            create_save_workout_tool(self._database, user_email),
            create_get_workouts_tool(self._database, user_email),
            create_get_workouts_raw_tool(self._database, user_email),
            # Nutrition
            create_save_nutrition_tool(self._database, user_email),
            create_get_nutrition_tool(self._database, user_email),
            create_sync_nutrition_text_tool(self._database, user_email),
            create_get_nutrition_raw_tool(self._database, user_email),
            # Composition
            create_save_composition_tool(self._database, user_email),
            create_get_composition_tool(self._database, user_email),
            create_get_body_composition_raw_tool(self._database, user_email),
            # Metabolism
            create_get_metabolism_tool(self._database, user_email),
            create_update_tdee_params_tool(self._database, user_email),
            create_reset_tdee_tracking_tool(self._database, user_email),
            # Plan - read + write
            create_get_plan_tool(self._database, user_email),
            create_get_plan_status_tool(self._database, user_email),
            create_update_plan_discovery_tool(self._database, user_email),
            create_create_plan_from_discovery_tool(self._database, user_email),
            create_update_plan_section_tool(self._database, user_email),
            create_record_plan_review_tool(self._database, user_email),
            create_plan_help_tool(self._database, user_email),
            # Plan training program (read-only, domain-specific)
            create_get_plan_training_program_tool(self._database, user_email),
        ]

        # Hevy tools: only expose when user has Hevy integration enabled
        if hevy_enabled:
            tools.extend([
                create_list_hevy_routines_tool(hevy_service, self._database, user_email),
                create_create_hevy_routine_tool(hevy_service, self._database, user_email),
                create_update_hevy_routine_tool(hevy_service, self._database, user_email),
                create_search_hevy_exercises_tool(hevy_service, self._database, user_email),
                create_replace_hevy_exercise_tool(hevy_service, self._database, user_email),
                create_get_hevy_routine_detail_tool(
                    hevy_service, self._database, user_email
                ),
                create_set_routine_rest_and_ranges_tool(
                    hevy_service, self._database, user_email
                ),
                create_trigger_hevy_import_tool(hevy_service, self._database, user_email),
            ])

        if self._qdrant_client is not None:
            tools.extend(
                [
                    create_save_memory_tool(self._qdrant_client, user_email),
                    create_search_memory_tool(self._qdrant_client, user_email),
                    create_list_raw_memories_tool(self._qdrant_client, user_email),
                    create_update_memory_tool(self._qdrant_client, user_email),
                    create_delete_memory_tool(self._qdrant_client, user_email),
                    create_delete_memories_batch_tool(self._qdrant_client, user_email),
                    create_get_memories_raw_tool(self._qdrant_client, user_email),
                ]
            )

        tools.extend(
            [
                # Events
                create_create_event_tool(self._database.database, user_email),
                create_list_events_tool(self._database.database, user_email),
                create_delete_event_tool(self._database.database, user_email),
                create_update_event_tool(self._database.database, user_email),
                create_get_events_raw_tool(self._database, user_email),
            ]
        )

        return tools

    def get_llm_stream_timeout_seconds(self) -> float:
        """Returns the maximum streaming time allowed for one LLM response."""
        return float(settings.LLM_STREAM_TIMEOUT_SECONDS)

    # pylint: disable=too-many-locals,too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-branches,too-many-statements
    async def send_message_ai(
        self,
        user_email: str,
        user_input: str,
        background_tasks: Optional[BackgroundTasks] = None,
        message_options: dict | None = None,
    ):
        """
        Generates LLM response using the latest chat window only.
        This function assumes one chat session per user (user_email is used as session_id).

        Args:
            user_email (str): The user's email, also used as session ID.
            user_input (str): The user's input message.

        Yields:
            str: Individual chunks of the AI trainer's response.
        """
        logger.info("Generating workout stream for user: %s", user_email)
        image_payloads = (message_options or {}).get("image_payloads")

        profile = await asyncio.wrap_future(
            self._executor.submit(self.get_or_create_user_profile, user_email)
        )
        trainer_profile_obj = await asyncio.wrap_future(
            self._executor.submit(
                self.get_or_create_trainer_profile, user_email, profile
            )
        )

        needs_cycle_reset = self.check_message_limits(profile)

        metabolism_data = await asyncio.to_thread(
            AdaptiveTDEEService(self._database).calculate_tdee,
            user_email,
        )
        plan = await asyncio.to_thread(self._database.get_plan, user_email)
        discovery = await asyncio.to_thread(self._database.get_plan_discovery, user_email)
        progress = (
            await asyncio.to_thread(build_progress_snapshot, plan, self._database)
            if plan
            else None
        )
        enriched_plan_snapshot = build_plan_prompt_snapshot(plan, discovery, progress)
        recent_history = (
            await asyncio.to_thread(
                self._database.get_window_memory(
                    session_id=user_email,
                    k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
                ).load_memory_variables,
                {},
            )
        ).get("chat_history", [])
        approval_context = self.detect_explicit_plan_execution(
            user_input=user_input,
            recent_history=recent_history,
            plan_snapshot=enriched_plan_snapshot,
        )

        input_data = self.prompt_builder.build_input_data(
            profile=profile,
            trainer_profile_summary=trainer_profile_obj.get_trainer_profile_summary(),
            user_profile_summary=profile.get_profile_summary(),
            formatted_history_msgs=self.format_history_as_messages(recent_history),
            user_input=user_input,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            agenda_events=await asyncio.to_thread(
                EventRepository(self._database.database).get_active_events, user_email
            ),
            plan_snapshot=enriched_plan_snapshot,
            metabolism_data=metabolism_data,
        )
        input_data["user_locale"] = trainer_profile_obj.preferred_language or "pt-BR"
        if approval_context:
            input_data = self.apply_explicit_plan_execution_context(
                input_data,
                approval_context,
            )
        if image_payloads:
            input_data["user_images"] = image_payloads

        yield self.format_sse_event("status", {"stage": "preparing_context"})

        raw_response: list[str] = []
        tool_events: list[dict] = []
        stream_failed = False
        tool_summary: dict[str, list[str]] | None = None
        try:
            async with asyncio.timeout(self.get_llm_stream_timeout_seconds()):
                yield self.format_sse_event("status", {"stage": "using_tools"})
                async for chunk in self._llm_client.stream_with_tools(
                    prompt_template=self.prompt_builder.get_prompt_template(
                        input_data,
                        bool((message_options or {}).get("is_telegram", False)),
                    ),
                    input_data=input_data,
                    tools=self.get_tools(user_email),
                    model_override=settings.OPENROUTER_CHAT_MODEL,
                    user_email=user_email,
                    log_callback=self.get_log_callback(background_tasks),
                    temperature=0.2,
                    max_tokens=4096,
                    provider_sort="throughput",
                    reasoning={"effort": "low", "exclude": True},
                    parallel_tool_calls=False,
                ):
                    if isinstance(chunk, dict):
                        if chunk.get("type") == "tool_result":
                            tool_events.append(chunk)
                        elif chunk.get("type") == "tools_summary":
                            tool_summary = {"tools_called": chunk.get("tools_called", [])}
                        elif chunk.get("type") == "stream_error":
                            stream_failed = True
                        continue
                    if not isinstance(chunk, str):
                        continue
                    raw_response.append(chunk)
        except TimeoutError:
            logger.error(
                "LLM stream timeout for user %s after %ss",
                user_email,
                self.get_llm_stream_timeout_seconds(),
            )
            yield self.format_sse_event(
                "error",
                {
                    "message": self._safe_user_facing_error_message(
                        input_data.get("user_locale")
                    )
                },
            )
            return

        if stream_failed:
            logger.warning(
                "LLM stream failed for user %s; skipping history persistence.",
                user_email,
            )
            yield self.format_sse_event(
                "error",
                {
                    "message": self._safe_user_facing_error_message(
                        input_data.get("user_locale")
                    )
                },
            )
            return

        assistant_draft = self.strip_internal_wrappers("".join(raw_response))
        outcome_summary = self.summarize_tool_events(tool_events)
        if tool_summary:
            outcome_summary["tools_called"] = tool_summary.get("tools_called", [])

        if approval_context:
            final_response = self.render_explicit_plan_execution_response(
                approval_context=approval_context,
                tool_events=tool_events,
                user_locale=input_data.get("user_locale", "pt-BR"),
            )
            yield self.format_sse_event("status", {"stage": "writing_reply"})
            yield self.format_sse_event("delta", {"text": final_response})
            yield self.format_sse_event("status", {"stage": "saving"})
            await self.finalize_ai_response(
                user_email=user_email,
                user_input=user_input,
                final_response=final_response,
                metadata={
                    "trainer_type": trainer_profile_obj.trainer_type or "atlas",
                    "needs_cycle_reset": needs_cycle_reset,
                    "background_tasks": background_tasks,
                    "log_callback": self.get_log_callback(background_tasks),
                    "user_images": image_payloads,
                },
            )
            yield self.format_sse_event(
                "done",
                {"text": final_response, "persisted": True},
            )
            return

        final_input = await self.build_final_response_input(
            user_email=user_email,
            profile=profile,
            user_input=user_input,
            runtime_context_json=input_data.get("runtime_context_json", "{}"),
            user_locale=input_data.get("user_locale", "pt-BR"),
            tool_summary=outcome_summary,
            assistant_draft=assistant_draft,
            explicit_plan_approval=False,
            plan_execution_mode=input_data.get("plan_execution_mode", "none"),
            required_plan_tool=input_data.get("required_plan_tool", "none"),
        )

        yield self.format_sse_event("status", {"stage": "writing_reply"})

        final_response_chunks: list[str] = []
        final_stream_buffer = ""
        final_stream_failed = False

        async for chunk in self._llm_client.stream_with_tools(
            prompt_template=self.build_final_response_prompt(),
            input_data=final_input,
            tools=[],
            model_override=settings.OPENROUTER_CHAT_MODEL,
            user_email=user_email,
            log_callback=self.get_log_callback(background_tasks),
            temperature=0.2,
            max_tokens=512,
            provider_sort="latency",
            reasoning={"effort": "low", "exclude": True},
            run_name="chat.final",
            mode="final",
        ):
            if isinstance(chunk, dict):
                if chunk.get("type") == "stream_error":
                    final_stream_failed = True
                continue
            if not isinstance(chunk, str):
                continue
            final_response_chunks.append(chunk)
            final_stream_buffer += chunk
            visible, final_stream_buffer = self.split_stream_visible_text(final_stream_buffer)
            if visible:
                yield self.format_sse_event("delta", {"text": visible})

        if final_stream_buffer:
            cleaned_tail = self.strip_internal_wrappers(final_stream_buffer)
            if cleaned_tail:
                final_response_chunks.append(cleaned_tail)
                yield self.format_sse_event("delta", {"text": cleaned_tail})

        final_response = self.strip_internal_wrappers("".join(final_response_chunks)).strip()
        final_response = self.enforce_plan_update_truth_policy(
            final_response=final_response,
            tool_events=tool_events,
            user_locale=input_data.get("user_locale"),
        )
        if approval_context and self._contains_reconfirmation_request(final_response):
            final_response = self.render_explicit_plan_execution_response(
                approval_context=approval_context,
                tool_events=tool_events,
                user_locale=input_data.get("user_locale", "pt-BR"),
            )

        if final_stream_failed or not final_response:
            logger.warning(
                "Final response round failed or returned empty output for user %s",
                user_email,
            )
            yield self.format_sse_event(
                "error",
                {
                    "message": self._safe_user_facing_error_message(
                        input_data.get("user_locale")
                    )
                },
            )
            return

        yield self.format_sse_event("status", {"stage": "saving"})
        await self.finalize_ai_response(
            user_email=user_email,
            user_input=user_input,
            final_response=final_response,
            metadata={
                "trainer_type": trainer_profile_obj.trainer_type or "atlas",
                "needs_cycle_reset": needs_cycle_reset,
                "background_tasks": background_tasks,
                "log_callback": self.get_log_callback(background_tasks),
                "user_images": image_payloads,
            },
        )
        yield self.format_sse_event(
            "done",
            {"text": final_response, "persisted": True},
        )

    async def finalize_ai_response(
        self,
        *,
        user_email: str,
        user_input: str,
        final_response: str,
        metadata: dict,
    ):
        """Internal helper to log response, increment counts and save history."""
        # Flatten response for single-line logging
        flat_response = final_response.replace("\n", "\\n")
        log_response = (
            (flat_response[:500] + "...") if len(flat_response) > 500 else flat_response
        )
        logger.debug("LLM responded with: %s", log_response)

        # Detect error responses
        if final_response.startswith("Error processing request:"):
            logger.warning(
                "Error response for user %s, skipping history save.", user_email
            )
            return

        bg_tasks = metadata.get("background_tasks")
        train_type = metadata.get("trainer_type", "atlas")
        reset = metadata.get("needs_cycle_reset", False)
        user_images = metadata.get("user_images")

        if bg_tasks:
            # Async FastAPI environment
            bg_tasks.add_task(self.increment_counts, user_email, reset)
            bg_tasks.add_task(
                self.add_to_mongo_history,
                user_email,
                user_input,
                final_response,
                {"trainer_type": train_type, "user_images": user_images},
            )
            logger.info("Scheduled background tasks for user: %s", user_email)
        else:
            # Fallback for sync callers (like Telegram)
            self.increment_counts(user_email, reset)
            self.add_to_mongo_history(
                user_email,
                user_input,
                final_response,
                {"trainer_type": train_type, "user_images": user_images},
            )

    def send_message_sync(
        self,
        user_email: str,
        user_input: str,
        is_telegram: bool = False,
        image_payloads: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Synchronous version of send_message_ai for Telegram.
        Returns complete response instead of streaming.
        Also saves to MongoDB history.

        Args:
            user_email: User's email address.
            user_input: User's message text.

        Returns:
            Complete AI response as string.
        """

        async def collect_response():
            response_parts = []
            # Pass None to force sync fallback (line 550-554)
            # that calls _add_to_mongo_history() directly
            # This is necessary because BackgroundTasks only execute in HTTP response context,
            # not in async webhook handlers like Telegram

            async for chunk in self.send_message_ai(
                user_email=user_email,
                user_input=user_input,
                background_tasks=None,
                message_options={
                    "is_telegram": is_telegram,
                    "image_payloads": image_payloads,
                },
            ):
                if isinstance(chunk, str):
                    response_parts.append(chunk)

            return "".join(response_parts)

        try:
            # Try to run in existing loop or create new one
            return asyncio.run(collect_response())
        except RuntimeError:
            # Fallback if loop is already running (e.g. in some specific test environments)
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is tricky in sync code.
                # But pytest benchmarks usually don't run their own loop during the call.
                import nest_asyncio  # type: ignore # pylint: disable=import-error,import-outside-toplevel

                nest_asyncio.apply()
                return loop.run_until_complete(collect_response())
            return loop.run_until_complete(collect_response())

    async def analyze_workout_async(
        self,
        user_email: str,
        workout_summary: str,
    ) -> str:
        """
        Gera análise de treino de forma assíncrona (para background tasks).

        Usa o fluxo completo da IA com memória, perfil e personalidade do trainer,
        mas sem BackgroundTasks (não streama para usuário).

        Args:
            user_email: Email do usuário
            workout_summary: Resumo do treino a ser analisado

        Returns:
            Análise completa da IA como string
        """
        # Prompt que simula pergunta do usuário
        user_input = (
            f"Analisou meu último treino: {workout_summary}. "
            "Pode dar uma análise completa?"
        )

        # Coleta resposta sem streaming
        response_parts = []
        async for chunk in self.send_message_ai(
            user_email=user_email,
            user_input=user_input,
            background_tasks=None,  # Sem BackgroundTasks (não envia para SSE)
            message_options={"is_telegram": False},  # Resposta detalhada
        ):
            if isinstance(chunk, str):
                response_parts.append(chunk)

        response = "".join(response_parts)

        # Log prompt to database (same as regular chat prompts)
        self._database.prompts.log_prompt(
            user_email=user_email,
            prompt_data={
                "source": "async_analysis",
                "user_input": user_input,
                "response": response,
                "workout_summary": workout_summary,
            },
        )

        return response

    def delete_memory(self, memory_id: str, _user_email: str) -> bool:
        """
        Deletes a specific memory from Qdrant.
        """
        if self._qdrant_client is None:
            logger.error("Qdrant client not initialized for deletion")
            return False

        try:
            self._qdrant_client.delete(
                settings.QDRANT_COLLECTION_NAME, points_selector=[memory_id]
            )
            return True
        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Failed to delete memory %s: %s", memory_id, e)
            raise

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        """
        Retrieves a specific memory by ID from Qdrant.
        """
        if self._qdrant_client is None:
            return None

        try:
            points = self._qdrant_client.retrieve(
                settings.QDRANT_COLLECTION_NAME, ids=[memory_id]
            )
            return point_to_dict(points[0]) if points else None
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get memory %s: %s", memory_id, e)
            return None

    async def get_memories_paginated(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Delegates to memory_service."""
        if self._qdrant_client is None:
            return [], 0

        return paginate_memories(
            user_id,
            page,
            page_size,
            self._qdrant_client,
            settings.QDRANT_COLLECTION_NAME,
        )

    async def add_memory(
        self,
        text: str,
        user_id: str,
        translations: dict[str, str] | None = None,
    ) -> str:
        """Adds a memory to Qdrant."""
        if self._qdrant_client is None:
            raise HTTPException(status_code=500, detail="Qdrant not initialized")

        return service_add_memory(
            user_id=user_id,
            memory_data={"text": text, "translations": translations},
            qdrant_client=self._qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )
