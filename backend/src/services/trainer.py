"""AI trainer facade backed by the Pydantic AI chat runtime."""

from __future__ import annotations

import asyncio
import json
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import BackgroundTasks, HTTPException

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.core.config import settings
from src.core.logs import logger
from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan
from src.services.ai_chat.runner import ChatTurnRunner
from src.services.ai_chat.sse import format_sse_event
from src.services.database import MongoDatabase
from src.services.memory_service import (
    add_memory as service_add_memory,
    get_memories_paginated as paginate_memories,
)
from src.utils.date_utils import parse_cycle_start
from src.utils.qdrant_utils import point_to_dict


class AITrainerBrain:  # pylint: disable=too-many-public-methods
    """Facade used by API endpoints and Telegram."""

    _MSG_OPEN_PATTERN = re.compile(r'<msg(?:\s+data="[^"]*")?(?:\s+hora="[^"]*")?>')
    _TREINADOR_OPEN_PATTERN = re.compile(r'<treinador(?:\s+name="[^"]*")?>')
    USER_FACING_ERROR_MESSAGES = {
        "pt-BR": "Desculpe, ocorreu um erro interno. Tente novamente em instantes.",
        "en-US": "Sorry, an internal error occurred. Please try again shortly.",
        "es-ES": "Lo sentimos, ocurrió un error interno. Inténtalo de nuevo en breve.",
    }

    def __init__(
        self,
        database: MongoDatabase,
        llm_client=None,  # kept for dependency-construction compatibility
        qdrant_client=None,
    ):
        _ = llm_client
        self._database = database
        self._qdrant_client = qdrant_client
        self._runner = ChatTurnRunner(
            database=database,
            qdrant_client=qdrant_client,
        )

    @property
    def database(self) -> MongoDatabase:
        """Return the database instance."""
        return self._database

    @classmethod
    def get_user_facing_error_message(cls, locale: str | None) -> str:
        """Return localized safe error text."""
        return cls.USER_FACING_ERROR_MESSAGES.get(
            locale or "pt-BR", cls.USER_FACING_ERROR_MESSAGES["pt-BR"]
        )

    @staticmethod
    def normalize_text_for_intent(text: str) -> str:
        """Normalize free text for deterministic checks."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKD", text)
        ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
        ascii_text = ascii_text.lower()
        ascii_text = re.sub(r"[^a-z0-9\s]", " ", ascii_text)
        return re.sub(r"\s+", " ", ascii_text).strip()

    @classmethod
    def strip_internal_wrappers(cls, text: str) -> str:
        """Remove only protocol tags previously used by the old prompt."""
        if not text:
            return ""
        cleaned = cls._MSG_OPEN_PATTERN.sub("", text)
        cleaned = cleaned.replace("</msg>", "")
        cleaned = cls._TREINADOR_OPEN_PATTERN.sub("", cleaned)
        cleaned = cleaned.replace("</treinador>", "")
        return cleaned

    @classmethod
    def normalize_public_chat_text(cls, text: str) -> str:
        """Normalize persisted chat text before returning it to clients."""
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

    @staticmethod
    def format_sse_event(event: str, payload: dict | str) -> str:
        """Serialize one SSE event frame."""
        return format_sse_event(event, payload)

    def calculate_effective_limits(
        self, profile: UserProfile, plan
    ) -> tuple[int | None, int | None]:
        """Calculate subscription limits with custom overrides."""
        daily = plan.daily_limit
        monthly = plan.monthly_limit
        if profile.custom_message_limit is not None:
            if plan.daily_limit is not None:
                daily = profile.custom_message_limit
            elif plan.monthly_limit is not None:
                monthly = profile.custom_message_limit
        return daily, monthly

    def check_billing_cycle(
        self, profile: UserProfile, now: datetime
    ) -> tuple[bool, datetime | None]:
        """Return whether billing cycle counters need a reset."""
        if profile.current_billing_cycle_start is None:
            return True, None
        cycle_start = parse_cycle_start(profile.current_billing_cycle_start, now)
        return now - cycle_start >= timedelta(days=30), cycle_start

    def check_message_limits(self, profile: UserProfile) -> bool:
        """Verify message limits and return whether monthly cycle resets."""
        try:
            plan_name = SubscriptionPlan(profile.subscription_plan)
        except (ValueError, AttributeError):
            plan_name = SubscriptionPlan.FREE

        plan = SUBSCRIPTION_PLANS[plan_name]
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")
        needs_reset, cycle_start = self.check_billing_cycle(profile, now)
        validity = (
            profile.custom_trial_days
            if profile.custom_trial_days is not None
            else plan.validity_days
        )
        if validity is not None and cycle_start:
            if cycle_start.tzinfo is None:
                cycle_start = cycle_start.replace(tzinfo=timezone.utc)
            if now - cycle_start >= timedelta(days=validity):
                raise HTTPException(status_code=403, detail="TRIAL_EXPIRED")

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
            count = 0 if needs_reset else getattr(profile, "messages_sent_this_month", 0)
            if count >= eff_monthly:
                raise HTTPException(status_code=403, detail="LIMITE_MENSAGENS_MES")
        return needs_reset

    def increment_counts(self, user_email: str, new_cycle_start) -> None:
        """Increment message counters through the database facade."""
        self._database.increment_user_message_counts(user_email, new_cycle_start)

    def get_chat_history(
        self, session_id: str, limit: int = 20, offset: int = 0
    ) -> list[ChatHistory]:
        """Return public chat history with legacy wrappers removed."""
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
        """Return the stored user profile."""
        return self._database.get_user_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        """Persist a user profile."""
        self._database.save_user_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        """Partially update a user profile."""
        return self._database.update_user_profile_fields(email, fields)

    def get_or_create_user_profile(self, user_email: str) -> UserProfile:
        """Return existing user profile or create a safe default."""
        profile = self.get_user_profile(user_email)
        if profile:
            return profile
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
            target_weight=None,
            weekly_rate=0.0,
            notes=None,
        )
        self.save_user_profile(profile)
        return profile

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """Return trainer profile."""
        return self._database.get_trainer_profile(email)

    def save_trainer_profile(self, profile: TrainerProfile) -> None:
        """Persist trainer profile."""
        self._database.save_trainer_profile(profile)

    def ensure_trainer_allowed(
        self,
        user_email: str,
        plan_name: str,
        trainer_profile: TrainerProfile | None = None,
    ) -> str | None:
        """Ensure selected trainer is allowed for the subscription plan."""
        trainer_profile = trainer_profile or self.get_trainer_profile(user_email)
        if not trainer_profile:
            return None
        try:
            plan = SubscriptionPlan(plan_name)
        except (ValueError, AttributeError):
            plan = SubscriptionPlan.FREE
        allowed = SUBSCRIPTION_PLANS[plan].allowed_trainers
        if allowed and trainer_profile.trainer_type not in allowed:
            trainer_profile.trainer_type = allowed[0]
            self.save_trainer_profile(trainer_profile)
            return allowed[0]
        return None

    def get_or_create_trainer_profile(
        self, user_email: str, user_profile: UserProfile | None = None
    ) -> TrainerProfile:
        """Return existing trainer profile or create a default for the plan."""
        user_profile = user_profile or self.get_user_profile(user_email)
        plan_name = user_profile.subscription_plan if user_profile else "Free"
        profile = self._database.get_trainer_profile(user_email)
        if not profile:
            default_trainer = "gymbro" if plan_name == "Free" else "atlas"
            profile = TrainerProfile(user_email=user_email, trainer_type=default_trainer)
            self.save_trainer_profile(profile)
        else:
            self.ensure_trainer_allowed(user_email, plan_name, profile)
        return profile

    def add_to_mongo_history(
        self,
        user_email: str,
        user_input: str,
        response_text: str,
        metadata: dict | None = None,
    ) -> None:
        """Persist a public user/assistant message pair."""
        now = datetime.now().isoformat()
        metadata = metadata or {}
        trainer_type = metadata.get("trainer_type", "atlas")
        self._database.add_many_to_history(
            [
                ChatHistory(
                    sender=Sender.STUDENT,
                    text=user_input,
                    images=metadata.get("user_images"),
                    timestamp=now,
                    trainer_type=trainer_type,
                ),
                ChatHistory(
                    sender=Sender.TRAINER,
                    text=response_text,
                    timestamp=now,
                    trainer_type=trainer_type,
                ),
            ],
            user_email,
            trainer_type,
        )

    async def send_message_ai(
        self,
        user_email: str,
        user_input: str,
        background_tasks: Optional[BackgroundTasks] = None,
        message_options: dict | None = None,
    ):
        """Stream one Pydantic AI turn as SSE."""
        async for chunk in self._runner.stream_turn(
            user_email=user_email,
            user_input=user_input,
            background_tasks=background_tasks,
            message_options=message_options,
        ):
            yield chunk

    def send_message_sync(
        self,
        user_email: str,
        user_input: str,
        is_telegram: bool = False,
        image_payloads: list[dict[str, str]] | None = None,
    ) -> str:
        """Synchronous wrapper used by Telegram."""

        async def collect_response() -> str:
            response_parts: list[str] = []
            async for chunk in self.send_message_ai(
                user_email=user_email,
                user_input=user_input,
                background_tasks=None,
                message_options={
                    "is_telegram": is_telegram,
                    "image_payloads": image_payloads,
                },
            ):
                parsed = _parse_sse_delta_or_done(chunk)
                if parsed:
                    response_parts.append(parsed)
            return "".join(response_parts)

        try:
            return asyncio.run(collect_response())
        except RuntimeError:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio  # type: ignore # pylint: disable=import-error,import-outside-toplevel

                nest_asyncio.apply()
            return loop.run_until_complete(collect_response())

    async def analyze_workout_async(self, user_email: str, workout_summary: str) -> str:
        """Generate a chat-based workout analysis."""
        response_parts: list[str] = []
        async for chunk in self.send_message_ai(
            user_email=user_email,
            user_input=(
                f"Analise meu ultimo treino: {workout_summary}. "
                "Pode dar uma analise completa?"
            ),
            background_tasks=None,
            message_options={"is_telegram": False},
        ):
            parsed = _parse_sse_delta_or_done(chunk)
            if parsed:
                response_parts.append(parsed)
        response = "".join(response_parts)
        self._database.log_prompt(
            user_email,
            {
                "source": "async_analysis",
                "user_input": workout_summary,
                "response": response,
            },
        )
        return response

    def delete_memory(self, memory_id: str, _user_email: str) -> bool:
        """Delete a memory from Qdrant."""
        if self._qdrant_client is None:
            return False
        self._qdrant_client.delete(
            settings.QDRANT_COLLECTION_NAME, points_selector=[memory_id]
        )
        return True

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        """Return a memory by ID from Qdrant."""
        if self._qdrant_client is None:
            return None
        try:
            points = self._qdrant_client.retrieve(
                settings.QDRANT_COLLECTION_NAME, ids=[memory_id]
            )
            return point_to_dict(points[0]) if points else None
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get memory %s: %s", memory_id, exc)
            return None

    async def get_memories_paginated(
        self,
        user_id: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        """Return paginated memories from Qdrant."""
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
        """Add a memory to Qdrant."""
        if self._qdrant_client is None:
            raise HTTPException(status_code=500, detail="Qdrant not initialized")
        return service_add_memory(
            user_id=user_id,
            memory_data={"text": text, "translations": translations},
            qdrant_client=self._qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )


def _parse_sse_delta_or_done(chunk: str) -> str:
    """Extract visible text from one SSE frame."""
    if not isinstance(chunk, str) or not chunk.startswith("event:"):
        return chunk if isinstance(chunk, str) else ""
    event_name = ""
    data = ""
    for line in chunk.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            data = line.split(":", 1)[1].strip()
    if event_name != "delta" or not data:
        return ""
    try:
        payload = json.loads(data)
    except ValueError:
        return ""
    return str(payload.get("text") or "")
