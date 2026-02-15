"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.history_compactor import HistoryCompactor
from src.services.prompt_builder import PromptBuilder
from src.services.workout_tools import (
    create_save_workout_tool,
    create_get_workouts_tool,
)
from src.services.nutrition_tools import (
    create_save_nutrition_tool,
    create_get_nutrition_tool,
)
from src.services.composition_tools import (
    create_save_composition_tool,
    create_get_composition_tool,
)
from src.services.memory_tools import (
    create_save_memory_tool,
    create_search_memory_tool,
    create_list_raw_memories_tool,
    create_update_memory_tool,
    create_delete_memory_tool,
    create_delete_memories_batch_tool,
)
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile

class AITrainerBrain:
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """

    def __init__(self, database: MongoDatabase, llm_client: LLMClient, qdrant_client=None):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._qdrant_client = qdrant_client
        self.compactor = HistoryCompactor(database, llm_client)
        self.prompt_builder = PromptBuilder()
        self._executor = ThreadPoolExecutor(max_workers=10)

    @property
    def database(self) -> MongoDatabase:
        """Returns the database instance."""
        return self._database

    def _log_prompt_in_background(
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
            except Exception as e:
                logger.error("Error logging prompt to DB: %s", e)

    def _get_log_callback(self, background_tasks: Optional[BackgroundTasks] = None):
        """
        Returns a callback for LLMClient to use for logging.
        """

        def callback(email: str, data: dict):
            self._log_prompt_in_background(email, data, background_tasks)

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

    def save_trainer_profile(self, profile: TrainerProfile):
        """
        Saves a trainer profile to the database.
        """
        self._database.save_trainer_profile(profile)

    def _get_or_create_user_profile(self, user_email: str) -> UserProfile:
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

    def _get_or_create_trainer_profile(self, user_email: str) -> TrainerProfile:
        """Retrieves trainer profile or creates a default one if not found."""
        trainer_profile_obj = self._database.get_trainer_profile(user_email)
        if not trainer_profile_obj:
            logger.info(
                "Trainer profile not found, creating default for user: %s", user_email
            )
            trainer_profile_obj = TrainerProfile(
                user_email=user_email, trainer_type="atlas"
            )
            self.save_trainer_profile(trainer_profile_obj)
        return trainer_profile_obj

    def _add_to_mongo_history(
        self, user_email: str, user_input: str, response_text: str, trainer_type: str
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
        user_message = ChatHistory(
            sender=Sender.STUDENT,
            text=user_input,
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

    def _add_system_message_to_history(self, user_email: str, content: str):
        """
        Adds a SYSTEM message to history (e.g. tool feedback).
        """
        now = datetime.now().isoformat()
        # System messages don't need trainer_type
        system_msg = ChatHistory(sender=Sender.SYSTEM, text=content, timestamp=now)
        self._database.add_to_history(system_msg, user_email)
        logger.debug("Saved SYSTEM message to history: %s", content)

    def _sort_messages_by_timestamp(self, messages: list) -> list:
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

    def _format_history_as_messages(
        self,
        messages: list,
        current_trainer_type: str,
    ) -> list[BaseMessage]:
        """
        Formats LangChain messages into a list of BaseMessage objects for the prompt.
        Preserves the structural integrity of the history (Message objects) without
        adding prefixes, as LangChain already differentiates message types correctly.
        """
        if not messages:
            return []

        # Sort messages chronologically
        messages = self._sort_messages_by_timestamp(messages)

        formatted_msgs: list[BaseMessage] = []
        for msg in messages:
            # Extract timestamp prefix
            timestamp_prefix = ""
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                ts = msg.additional_kwargs.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        timestamp_prefix = f"[{dt.strftime('%d/%m %H:%M')}] "
                    except (ValueError, TypeError):
                        pass

            # Clean message content - single line
            raw_content = msg.content if msg.content else ""
            if not isinstance(raw_content, str):
                raw_content = str(raw_content)
            content = " ".join(raw_content.split())

            # Incorporate timestamp into content for LLM visibility
            content = f"{timestamp_prefix}{content}"

            # Check message type
            is_system = hasattr(msg, "type") and msg.type == "system"

            if is_system:
                # Skip system messages (tool results) - they were processed during their
                # original turn and should not consume context window slots.
                # This prevents tool metadata from misleading the LLM in future turns.
                continue

            elif isinstance(msg, HumanMessage):
                # Pass user messages as-is
                formatted_msgs.append(HumanMessage(content=content))

            elif isinstance(msg, AIMessage):
                # Pass AI messages as-is, preserving trainer_type in metadata if needed
                formatted_msgs.append(
                    AIMessage(content=content, additional_kwargs=msg.additional_kwargs)
                )
            else:
                # Fallback for unknown message types
                formatted_msgs.append(HumanMessage(content=content))

        return formatted_msgs

    async def send_message_ai(
        self,
        user_email: str,
        user_input: str,
        background_tasks: Optional[BackgroundTasks] = None,
        is_telegram: bool = False,
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

        import asyncio

        # Parallelize: profile retrieval (using shared executor)
        # We use wrap_future + await to avoid blocking the event loop
        future_user = self._executor.submit(
            self._get_or_create_user_profile, user_email
        )
        future_trainer = self._executor.submit(
            self._get_or_create_trainer_profile, user_email
        )

        # Memory retrieval is now async
        profile = await asyncio.wrap_future(future_user)
        trainer_profile_obj = await asyncio.wrap_future(future_trainer)

        # POC: Remove automatic memory injection. AI now manages memories explicitly via tools.
        # Mem0 background task still runs for comparison.
        relevant_memories_str = ""

        current_trainer_type = trainer_profile_obj.trainer_type or "atlas"

        # Get conversation memory with fixed window (V3 Strategy)
        # We rely on HistoryCompactor for long-term summarization, so we only need recent history here.
        conversation_memory = self._database.get_window_memory(
            session_id=user_email,
            k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,  # Typically 20-40 matches
        )

        # Load memory variables (includes summary + recent messages if buffer exceeded)
        # We use to_thread because this hits MongoDB synchronously via LangChain
        memory_vars = await asyncio.to_thread(
            conversation_memory.load_memory_variables, {}
        )
        chat_history_messages = memory_vars.get("chat_history", [])

        # Format structured history
        formatted_history_msgs = self._format_history_as_messages(
            chat_history_messages,
            current_trainer_type=current_trainer_type,
        )

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile_summary = profile.get_profile_summary()

        # Build input data using PromptBuilder
        input_data = self.prompt_builder.build_input_data(
            profile=profile,
            trainer_profile_summary=trainer_profile_summary,
            user_profile_summary=user_profile_summary,
            relevant_memories_str=relevant_memories_str,
            chat_history_summary="",  # Legacy (removed from template V3)
            formatted_history_msgs=formatted_history_msgs,
            user_input=user_input,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

        # Get prompt template using PromptBuilder
        prompt_template = self.prompt_builder.get_prompt_template(
            input_data, is_telegram=is_telegram
        )

        # Create workout tracking tools with injected dependencies
        save_workout_tool = create_save_workout_tool(self._database, user_email)
        get_workouts_tool = create_get_workouts_tool(self._database, user_email)

        # Create nutrition tracking tools
        save_nutrition_tool = create_save_nutrition_tool(self._database, user_email)
        get_nutrition_tool = create_get_nutrition_tool(self._database, user_email)

        # Create composition tracking tools
        save_composition_tool = create_save_composition_tool(self._database, user_email)
        get_composition_tool = create_get_composition_tool(self._database, user_email)

        # Create Hevy tools
        from src.services.hevy_tools import (
            create_list_hevy_routines_tool,
            create_create_hevy_routine_tool,
            create_update_hevy_routine_tool,
            create_search_hevy_exercises_tool,
            create_replace_hevy_exercise_tool,
            create_get_hevy_routine_detail_tool,
            create_set_routine_rest_and_ranges_tool,
        )
        from src.services.hevy_service import HevyService

        hevy_service = HevyService(workout_repository=self._database.workouts_repo)

        list_hevy_routines_tool = create_list_hevy_routines_tool(
            hevy_service, self._database, user_email
        )
        create_hevy_routine_tool = create_create_hevy_routine_tool(
            hevy_service, self._database, user_email
        )
        update_hevy_routine_tool = create_update_hevy_routine_tool(
            hevy_service, self._database, user_email
        )
        search_hevy_exercises_tool = create_search_hevy_exercises_tool(
            hevy_service, self._database, user_email
        )
        replace_hevy_exercise_tool = create_replace_hevy_exercise_tool(
            hevy_service, self._database, user_email
        )
        get_hevy_routine_detail_tool = create_get_hevy_routine_detail_tool(
            hevy_service, self._database, user_email
        )
        set_routine_rest_and_ranges_tool = create_set_routine_rest_and_ranges_tool(
            hevy_service, self._database, user_email
        )

        # Create profile management tools
        from src.services.profile_tools import (
            create_get_user_goal_tool,
            create_update_user_goal_tool,
        )

        get_user_goal_tool = create_get_user_goal_tool(self._database, user_email)
        update_user_goal_tool = create_update_user_goal_tool(self._database, user_email)

        # Create memory management tools (POC: AI-driven memory curation)
        # Pass mem0_client to ensure 768-dim embedding compatibility with existing vectors
        save_memory_tool = create_save_memory_tool(self._qdrant_client, user_email)
        search_memory_tool = create_search_memory_tool(self._qdrant_client, user_email)
        list_raw_memories_tool = create_list_raw_memories_tool(self._qdrant_client, user_email)
        update_memory_tool = create_update_memory_tool(self._qdrant_client, user_email)
        delete_memory_tool = create_delete_memory_tool(self._qdrant_client, user_email)
        delete_memories_batch_tool = create_delete_memories_batch_tool(self._qdrant_client, user_email)

        tools = [
            save_workout_tool,
            get_workouts_tool,
            save_nutrition_tool,
            get_nutrition_tool,
            save_composition_tool,
            get_composition_tool,
            list_hevy_routines_tool,
            create_hevy_routine_tool,
            update_hevy_routine_tool,
            search_hevy_exercises_tool,
            replace_hevy_exercise_tool,
            get_hevy_routine_detail_tool,
            set_routine_rest_and_ranges_tool,
            get_user_goal_tool,
            update_user_goal_tool,
            save_memory_tool,
            search_memory_tool,
            list_raw_memories_tool,
            update_memory_tool,
            delete_memory_tool,
            delete_memories_batch_tool,
        ]

        # Create log callback
        log_callback = self._get_log_callback(background_tasks)

        full_response = []
        async for chunk in self._llm_client.stream_with_tools(
            prompt_template=prompt_template,
            input_data=input_data,
            tools=tools,
            user_email=user_email,
            log_callback=log_callback,
        ):
            # Check for System Feedback (Dict)
            if isinstance(chunk, dict):
                if chunk.get("type") == "tool_result":
                    tool_name = chunk.get("tool_name")
                    content = chunk.get("content")
                    # Log tool result for audit trail (in prompt_logs), but don't save to chat history
                    # to avoid polluting the context window with tool metadata
                    logger.debug(
                        "Tool '%s' executed for %s. Result: %s",
                        tool_name,
                        user_email,
                        str(content)[:200]
                    )
                    continue
                elif chunk.get("type") == "tools_summary":
                    # Skip tools summary chunk
                    continue

            # It's a string chunk (AI Response)
            if isinstance(chunk, str):
                full_response.append(chunk)
                yield chunk

        final_response = "".join(full_response)
        # Flatten response for single-line logging
        flat_response = final_response.replace("\n", "\\n")
        log_response = (
            (flat_response[:500] + "...") if len(flat_response) > 500 else flat_response
        )
        logger.debug("LLM responded with: %s", log_response)

        # Detect error responses - don't save to history or trigger background tasks
        is_error_response = final_response.startswith("Error processing request:")
        if is_error_response:
            logger.warning(
                "Error response detected for user %s, skipping history save: %s",
                user_email,
                final_response[:100]
            )
            return

        if background_tasks:
            # Move DB saving to background to avoid blocking the generator completion
            background_tasks.add_task(
                self._add_to_mongo_history,
                user_email,
                user_input,
                final_response,
                current_trainer_type,
            )

            # Schedule History Compaction
            background_tasks.add_task(
                self.compactor.compact_history,
                user_email=user_email,
                active_window_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,  # Synced with window memory
                log_callback=log_callback,
            )

            logger.info(
                "Scheduled background tasks (Mongo + Compactor) for user: %s",
                user_email,
            )
        else:
            # Fallback for sync callers (like Telegram)
            self._add_to_mongo_history(
                user_email, user_input, final_response, current_trainer_type
            )
            # Note: is_error_response check above already returns before reaching here

    def send_message_sync(
        self, user_email: str, user_input: str, is_telegram: bool = False
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
        import asyncio

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
                is_telegram=is_telegram,
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
        Gera análise de treino de forma assíncrona (para webhooks/background tasks).

        Usa o fluxo completo da IA com memória, perfil e personalidade do trainer,
        mas sem BackgroundTasks (não streama para usuário).

        Args:
            user_email: Email do usuário
            workout_summary: Resumo do treino a ser analisado

        Returns:
            Análise completa da IA como string
        """
        # Prompt que simula pergunta do usuário
        user_input = f"Analisou meu último treino: {workout_summary}. Pode dar uma análise completa?"

        # Coleta resposta sem streaming
        response_parts = []
        async for chunk in self.send_message_ai(
            user_email=user_email,
            user_input=user_input,
            background_tasks=None,  # Sem BackgroundTasks (não envia para SSE)
            is_telegram=False,  # Resposta detalhada (não resumida)
        ):
            if isinstance(chunk, str):
                response_parts.append(chunk)

        response = "".join(response_parts)

        # Log prompt to database (same as regular chat prompts)
        self._database.prompts.log_prompt(
            user_email=user_email,
            prompt_data={
                "source": "webhook_analysis",
                "user_input": user_input,
                "response": response,
                "workout_summary": workout_summary,
            },
        )

        return response

    def get_all_memories(self, user_id: str, limit: int = 50) -> list[dict]:
        """
        Retrieves all memories for a given user from Mem0.

        Args:
            user_id (str): The user's email/ID.
            limit (int): Maximum number of memories to return.

        Returns:
            list[dict]: List of memory dictionaries with id, memory, created_at, updated_at.
        """
        logger.info("Retrieving memories for user: %s (limit: %d)", user_id, limit)
        try:
            result = self._memory.get_all(user_id=user_id)
            logger.debug("Raw Mem0 get_all response type: %s", type(result))

            # Debug: log actual response structure
            if isinstance(result, dict):
                logger.debug("Mem0 response keys: %s", result.keys())
                logger.debug("Mem0 full response: %s", result)

            if isinstance(result, list):
                raw_memories = result
            elif isinstance(result, dict):
                raw_memories = result.get("memories", result.get("results", []))
            else:
                raw_memories = []
                
            # Ensure it's a list of dicts for Pyright
            memories: list[dict] = [m for m in raw_memories if isinstance(m, dict)]
            
            logger.info(
                "Retrieved %d memories from Mem0 for user: %s", len(memories), user_id
            )

            # Sort by created_at descending (newest first) and limit
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            limited_memories = memories[:limit]

            logger.debug(
                "Returning %d memories after sorting and limiting",
                len(limited_memories),
            )
            return limited_memories
        except Exception as e:
            logger.error("Failed to retrieve memories for user %s: %s", user_id, e)
            raise

    def delete_memory(self, memory_id: str, user_email: str) -> bool:
        """
        Deletes a specific memory from Qdrant (POC: supports both Mem0 and AI-created memories).

        Args:
            memory_id (str): The unique ID of the memory to delete.
            user_email (str): The user's email (for authorization verification).

        Returns:
            bool: True if deletion was successful.
        """
        logger.info("Attempting to delete memory: %s for user: %s", memory_id, user_email)
        try:
            # Use Qdrant directly to support both Mem0 and tool-created memories
            # All memories share same base collection, filtered by user_id in payload
            self._qdrant_client.delete(
                settings.QDRANT_COLLECTION_NAME, points_selector=[memory_id]
            )
            logger.info("Successfully deleted memory: %s", memory_id)
            return True
        except Exception as e:
            logger.error("Failed to delete memory %s: %s", memory_id, e)
            raise

    def get_memory_by_id(self, memory_id: str, user_email: str) -> dict | None:
        """
        Retrieves a specific memory by ID from Qdrant (POC: supports both Mem0 and AI-created memories).

        Args:
            memory_id (str): The unique ID of the memory.
            user_email (str): The user's email (for authorization verification).

        Returns:
            dict | None: The memory object if found, otherwise None.
        """
        try:
            # Use Qdrant directly to support both Mem0 and tool-created memories
            # All memories share same base collection, filtered by user_id in payload
            points = self._qdrant_client.retrieve(settings.QDRANT_COLLECTION_NAME, ids=[memory_id])

            if not points:
                return None

            point = points[0]
            payload = point.payload or {}

            # Return in same format as Mem0 would
            return {
                "id": payload.get("id", str(point.id)),
                "memory": payload.get("memory", ""),
                "user_id": payload.get("user_id", user_email),
                "created_at": payload.get("created_at"),
                "updated_at": payload.get("updated_at"),
            }
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to get memory %s: %s", memory_id, e)
            return None

    def get_memories_paginated(
        self,
        user_id: str,
        page: int,
        page_size: int,
        qdrant_client,
        collection_name: str,
    ) -> tuple[list[dict], int]:
        """
        Retrieves memories for a user with pagination via Qdrant scroll.

        Args:
            user_id: The user's email/ID
            page: Page number (1-indexed)
            page_size: Number of memories per page
            qdrant_client: Qdrant client for direct access
            collection_name: Qdrant collection name

        Returns:
            tuple: (list of memories, total count)
        """
        # pylint: disable=import-outside-toplevel,too-many-arguments,too-many-locals
        from qdrant_client import models as qdrant_models

        logger.info(
            "Retrieving paginated memories for user: %s (page: %d, size: %d)",
            user_id,
            page,
            page_size,
        )

        try:
            # Filter by user_id
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id", match=qdrant_models.MatchValue(value=user_id)
                    )
                ]
            )

            # Get total count for this user
            count_result = qdrant_client.count(
                collection_name=collection_name, count_filter=user_filter
            )
            total = count_result.count
            logger.debug("Total memories for user %s: %d", user_id, total)

            if total == 0:
                logger.info("No memories found for user: %s", user_id)
                return [], 0

            # Calculate offset for pagination
            offset = (page - 1) * page_size

            # Get all points for this user and manually paginate
            # Note: Qdrant scroll doesn't support direct offset, so we scroll and skip
            all_points = []
            next_offset = None

            while True:
                points, next_offset = qdrant_client.scroll(
                    collection_name=collection_name,
                    scroll_filter=user_filter,
                    limit=100,  # Fetch in batches
                    offset=next_offset,
                    with_payload=True,
                )
                all_points.extend(points)
                if next_offset is None:
                    break

            # Sort by created_at descending (newest first)
            all_points.sort(
                key=lambda p: p.payload.get("created_at", "") if p.payload else "",
                reverse=True,
            )

            # Apply pagination
            paginated_points = all_points[offset : offset + page_size]

            # Convert to memory dictionaries
            memories = []
            for point in paginated_points:
                payload = point.payload or {}
                memories.append(
                    {
                        "id": payload.get("id", str(point.id)),
                        "memory": payload.get("memory", payload.get("data", "")),
                        "created_at": payload.get("created_at"),
                        "updated_at": payload.get("updated_at"),
                    }
                )

            logger.info(
                "Returning %d memories for user %s (page %d of %d)",
                len(memories),
                user_id,
                page,
                (total + page_size - 1) // page_size,
            )
            return memories, total

        except Exception as e:
            logger.error(
                "Failed to retrieve paginated memories for user %s: %s", user_id, e
            )
            raise
