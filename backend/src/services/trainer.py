"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks, HTTPException
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from src.core.config import settings
from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.history_compactor import HistoryCompactor
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
from src.services.profile_tools import (
    create_get_user_goal_tool,
    create_update_user_goal_tool,
)
from src.repositories.event_repository import EventRepository
from src.services.memory_service import (
    get_memories_paginated as paginate_memories,
    add_memory as service_add_memory,
)
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.workout_log import WorkoutLog

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


class AITrainerBrain:  # pylint: disable=too-many-public-methods
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """

    def __init__(
        self,
        database: MongoDatabase,
        llm_client: LLMClient,
        qdrant_client: Optional["QdrantClient"] = None,
    ):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._qdrant_client = qdrant_client
        self.compactor = HistoryCompactor(database, llm_client)
        self.prompt_builder = PromptBuilder()
        self._executor = ThreadPoolExecutor(max_workers=10)

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
        return self._database.get_chat_history(session_id, limit, offset)

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
                weight=70.0,
                height=175,
                goal="Melhorar condicionamento",
                goal_type="maintain",
                # Mandatory fields for Mypy/Pyright
                target_weight=None,
                weekly_rate=0.5,
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
        self._database.add_to_history(user_message, user_email, trainer_type)
        self._database.add_to_history(ai_message, user_email, trainer_type)
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

    def get_tools(self, user_email: str) -> list[BaseTool]:
        """
        Creates and returns a list of tools available to the AI.
        """
        hevy_service = HevyService(workout_repository=self._database.workouts_repo)

        tools = [
            # Workout
            create_save_workout_tool(self._database, user_email),
            create_get_workouts_tool(self._database, user_email),
            # Nutrition
            create_save_nutrition_tool(self._database, user_email),
            create_get_nutrition_tool(self._database, user_email),
            create_sync_nutrition_text_tool(self._database, user_email),
            # Composition
            create_save_composition_tool(self._database, user_email),
            create_get_composition_tool(self._database, user_email),
            # Hevy
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
            # User Goals
            create_get_user_goal_tool(self._database, user_email),
            create_update_user_goal_tool(self._database, user_email),
            # Metabolism
            create_get_metabolism_tool(self._database, user_email),
            create_update_tdee_params_tool(self._database, user_email),
            create_reset_tdee_tracking_tool(self._database, user_email),
        ]

        if self._qdrant_client is not None:
            tools.extend(
                [
                    create_save_memory_tool(self._qdrant_client, user_email),
                    create_search_memory_tool(self._qdrant_client, user_email),
                    create_list_raw_memories_tool(self._qdrant_client, user_email),
                    create_update_memory_tool(self._qdrant_client, user_email),
                    create_delete_memory_tool(self._qdrant_client, user_email),
                    create_delete_memories_batch_tool(self._qdrant_client, user_email),
                ]
            )

        tools.extend(
            [
                # Events
                create_create_event_tool(self._database.database, user_email),
                create_list_events_tool(self._database.database, user_email),
                create_delete_event_tool(self._database.database, user_email),
                create_update_event_tool(self._database.database, user_email),
            ]
        )

        return tools

    async def send_message_ai(
        self,
        user_email: str,
        user_input: str,
        background_tasks: Optional[BackgroundTasks] = None,
        message_options: dict | None = None,
    ):
        """
        Generates LLM response, summarizing history if needed.
        This function assumes one chat session per user (user_email is used as session_id).

        If the conversation history exceeds 20 messages, it will:
        1. Separate old messages (first 10) from recent messages (remaining)
        2. Summarize old messages and merge with existing summary
        3. Prune the chat history, keeping only recent messages
        4. Update the conversation summary in the database

        Args:
            user_email (str): The user's email, also used as session ID.
            user_input (str): The user's input message.

        Yields:
            str: Individual chunks of the AI trainer's response.
        """
        logger.info("Generating workout stream for user: %s", user_email)
        options = message_options or {}
        is_telegram = bool(options.get("is_telegram", False))
        image_payloads = options.get("image_payloads")

        # 1. Retrieve profiles (sequentially to avoid redundant DB calls and plan mismatch)
        profile = await asyncio.wrap_future(
            self._executor.submit(self.get_or_create_user_profile, user_email)
        )
        trainer_profile_obj = await asyncio.wrap_future(
            self._executor.submit(
                self.get_or_create_trainer_profile, user_email, profile
            )
        )

        # 2. Check limits
        needs_cycle_reset = self.check_message_limits(profile)

        # 3. Memory & History
        chat_history_messages = (
            await asyncio.to_thread(
                self._database.get_window_memory(
                    session_id=user_email,
                    k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
                ).load_memory_variables,
                {},
            )
        ).get("chat_history", [])

        # 4. Build input data
        input_data = self.prompt_builder.build_input_data(
            profile=profile,
            trainer_profile_summary=trainer_profile_obj.get_trainer_profile_summary(),
            user_profile_summary=profile.get_profile_summary(),
            chat_history_summary="",
            formatted_history_msgs=self.format_history_as_messages(
                chat_history_messages
            ),
            user_input=user_input,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            agenda_events=await asyncio.to_thread(
                EventRepository(self._database.database).get_active_events, user_email
            ),
        )
        if image_payloads:
            input_data["user_images"] = image_payloads

        full_response: list[str] = []
        async for chunk in self._llm_client.stream_with_tools(
            prompt_template=self.prompt_builder.get_prompt_template(
                input_data, is_telegram
            ),
            input_data=input_data,
            tools=self.get_tools(user_email),
            user_email=user_email,
            log_callback=self.get_log_callback(background_tasks),
        ):
            if isinstance(chunk, str):
                full_response.append(chunk)
                yield chunk

        await self.finalize_ai_response(
            user_email=user_email,
            user_input=user_input,
            final_response="".join(full_response),
            metadata={
                "trainer_type": trainer_profile_obj.trainer_type or "atlas",
                "needs_cycle_reset": needs_cycle_reset,
                "background_tasks": background_tasks,
                "log_callback": self.get_log_callback(background_tasks),
                "user_images": image_payloads,
            },
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
        callback = metadata.get("log_callback")
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
            bg_tasks.add_task(
                self.compactor.compact_history,
                user_email=user_email,
                active_window_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
                log_callback=callback,
                compaction_threshold=settings.COMPACTION_THRESHOLD,
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
            await self.compactor.compact_history(
                user_email=user_email,
                active_window_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
                log_callback=callback,
                compaction_threshold=settings.COMPACTION_THRESHOLD,
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
