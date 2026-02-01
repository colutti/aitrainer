"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from typing import Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from mem0 import Memory  # type: ignore

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.history_compactor import HistoryCompactor
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
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile


def _add_to_mem0_background(
    memory: Memory, user_email: str, user_input: str, response_text: str
):
    """
    Background task function to add conversation to Mem0 (long-term memory).
    This runs asynchronously to avoid blocking the response stream.

    Args:
        memory (Memory): The Mem0 Memory client instance.
        user_email (str): The user's email.
        user_input (str): The user's input message.
        response_text (str): The AI's response message.
    """
    try:
        # Format as conversation messages so Mem0 extracts facts cleaner
        messages = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response_text},
        ]
        memory.add(messages, user_id=user_email)
        logger.info(
            "Successfully added conversation turn to Mem0 for user: %s", user_email
        )
    except Exception as e:
        # Log error but don't crash - Mem0 storage is not critical for user experience
        logger.error("Failed to add memory to Mem0 for user %s: %s", user_email, e)


class AITrainerBrain:
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """

    def _format_date(self, date_str: str) -> str:
        """Helper to format date strings."""
        if not date_str:
            return "Data desc."
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m")
        except (ValueError, AttributeError):
            return "Data desc."

    def __init__(self, database: MongoDatabase, llm_client: LLMClient, memory: Memory):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._memory: Memory = memory
        self.compactor = HistoryCompactor(database, llm_client)

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
            background_tasks.add_task(self._database.log_prompt, user_email, prompt_data)
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

    def _get_prompt_template(
        self, input_data: dict, is_telegram: bool = False
    ) -> ChatPromptTemplate:
        """Constructs and returns the chat prompt template."""
        logger.debug("Constructing chat prompt template (is_telegram=%s).", is_telegram)

        # Base template from settings
        system_content = settings.PROMPT_TEMPLATE

        # 🛡️ DEFENSIVE INJECTION PATTERN (V3 Blindagem)
        # We move potentially 'dirty' content (with braces {}) to dedicated placeholders
        # to prevent LangChain from interpreting them as template variables.

        # 1. Long-Term Summary
        # Now positioned in template BEFORE Mem0 memories for better hierarchy
        user_profile = input_data.get("user_profile_obj")
        if user_profile and user_profile.long_term_summary:
            input_data["long_term_summary_section"] = (
                f"\n\n📜 [RESUMO DE LONGO PRAZO]:\n{user_profile.long_term_summary}"
            )
        else:
            input_data["long_term_summary_section"] = ""
        
        # Add current_date if not present (for tests)
        if "current_date" not in input_data:
            input_data["current_date"] = datetime.now().strftime("%Y-%m-%d")

        # 2. Recent History & Memories (Already placeholders in settings.PROMPT_TEMPLATE)
        # We ensure they are treated as values, not template parts.

        # REPLACE the string placeholder for history with nothing, 
        # because we will use MessagesPlaceholder for true history injection.
        system_content = system_content.replace("{chat_history_summary}", "")

        if is_telegram:
            system_content += (
                "\n\n--- \n"
                "⚠️ **FORMATO TELEGRAM (MOBILE)**: "
                "O usuário está enviando mensagens via Telegram. Responda de forma direta e concisa. "
                "Use Markdown simples (negrito e itálico). Evite tabelas muito largas ou blocos de código extensos que não cabem na tela do celular."
            )

        messages = [("system", system_content)]
        messages.append(MessagesPlaceholder(variable_name="chat_history"))
        messages.append(("human", "{user_message}"))

        prompt_template = ChatPromptTemplate.from_messages(messages)

        # Verify formatting works and log anatomy concisely
        try:
            rendered_prompt = prompt_template.format(**input_data)
            critical_check = (
                "✅ Presente"
                if "## 🚨 Fatos Críticos" in rendered_prompt
                else "❌ Ausente"
            )
            logger.debug(
                "🛡️ PROMPT ANATOMY CHECK: Critical Section: %s | Total Chars: %d",
                critical_check,
                len(rendered_prompt),
            )
        except KeyError as e:
            logger.error(
                "🛡️ CRITICAL: KeyError during prompt formation: %s. Likely unescaped braces in data.",
                e,
            )
            raise

        return prompt_template

    # _extract_conversation_text removed (obsolete)

    def get_chat_history(self, session_id: str) -> list[ChatHistory]:
        """
        Retrieves the chat history for a given session ID.

        Args:
            session_id (str): The session ID.

        Returns:
            list[ChatHistory]: A list of chat messages.
        """
        logger.debug("Attempting to retrieve chat history for session: %s", session_id)
        return self._database.get_chat_history(session_id)

    def _normalize_mem0_results(self, results, source: str) -> list[dict]:
        """Helper to normalize Mem0 results."""
        normalized = []
        data = results.get("results", []) if isinstance(results, dict) else results
        for mem in data:
            if text := mem.get("memory", ""):
                normalized.append(
                    {
                        "text": text,
                        "created_at": mem.get("created_at", ""),
                        "source": source,
                    }
                )
        return normalized

    def _retrieve_critical_facts(self, user_id: str) -> list[dict]:
        """
        Busca explícita por fatos críticos (saúde, lesões, objetivos) que devem ter precedência.
        Garante que 'alergia', 'lesão', etc. sejam recuperados mesmo se semântica falhar.
        Expanded keywords include: health, preferences, equipment, schedule, experience.
        """
        critical_keywords = (
            "alergia lesão dor objetivo meta restrição médico cirurgia "
            "preferência equipamento disponível horário treino experiência "
            "limitação físico histórico peso altura"
        )
        results = self._memory.search(user_id=user_id, query=critical_keywords, limit=10)  # Increased from 5 to 10
        return self._normalize_mem0_results(results, source="critical")

    def _retrieve_semantic_memories(
        self, user_id: str, query: str, limit: int = 10  # Increased from 5 to 10
    ) -> list[dict]:
        """Busca contexto semântico baseado no input atual."""
        results = self._memory.search(user_id=user_id, query=query, limit=limit)
        return self._normalize_mem0_results(results, source="semantic")

    def _retrieve_recent_memories(self, user_id: str, limit: int = 10) -> list[dict]:  # Increased from 5 to 10
        """Busca memórias recém-adicionadas (contexto temporal de curto prazo expandido)."""
        try:
            # get_all returns newest first usually
            results = self._memory.get_all(user_id=user_id, limit=limit)
            return self._normalize_mem0_results(results, source="recent")
        except Exception:
            return []

    def _retrieve_hybrid_memories(self, user_input: str, user_id: str) -> dict:
        """
        Retrieves memories using Hybrid Search (Critical + Semantic + Recent).
        Returns a structured dictionary to allow explicit prompt placement.
        """
        logger.debug("Retrieving HYBRID memories for user: %s", user_id)

        # Use ThreadPoolExecutor for parallel searches to reduce TTFT
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_critical = executor.submit(self._retrieve_critical_facts, user_id)
            future_semantic = executor.submit(
                self._retrieve_semantic_memories, user_id, user_input
            )
            future_recent = executor.submit(self._retrieve_recent_memories, user_id)

            critical = future_critical.result()
            semantic = future_semantic.result()
            recent = future_recent.result()

        # Deduplicate (prefer Critical > Semantic > Recent)
        seen_texts = set()
        unique_critical = []
        for m in critical:
            if m["text"] not in seen_texts:
                unique_critical.append(m)
                seen_texts.add(m["text"])

        unique_semantic = []
        for m in semantic:
            if m["text"] not in seen_texts:
                unique_semantic.append(m)
                seen_texts.add(m["text"])

        unique_recent = []
        for m in recent:
            if m["text"] not in seen_texts:
                unique_recent.append(m)
                seen_texts.add(m["text"])

        return {
            "critical": unique_critical,
            "semantic": unique_semantic,
            "recent": unique_recent,
        }

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
                gender="Masculino",
                age=30,
                weight=70.0,
                height=175,
                goal="Melhorar condicionamento",
                goal_type="maintain",
                # Mandatory fields for Mypy
                target_weight=None,
                weekly_rate=0.5,
                notes=None,
                long_term_summary=None,
                last_compaction_timestamp=None,
                hevy_api_key=None,
                hevy_enabled=False,
                hevy_last_sync=None,
                hevy_webhook_token=None,
                hevy_webhook_secret=None,
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

    def _format_memory_messages(
        self,
        messages: list,
        current_trainer_type: str,
    ) -> str:
        """
        Formats LangChain messages with trainer context for the prompt.
        Uses compact single-line format:
        [DD/MM HH:MM] 🧑 Aluno: msg
        [DD/MM HH:MM] 🏋️ VOCÊ (Treinador): msg
        [DD/MM HH:MM] 🏋️ EX-TREINADOR [Type]: msg
        [DD/MM HH:MM] ⚙️ SISTEMA (Log): msg
        """
        if not messages:
            return "Nenhuma mensagem anterior."

        # Sort messages chronologically
        messages = self._sort_messages_by_timestamp(messages)

        formatted = []
        for msg in messages:
            # Extract timestamp if available
            timestamp_str = ""
            if hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
                ts = msg.additional_kwargs.get("timestamp", "")
                if ts:
                    try:
                        dt = datetime.fromisoformat(ts)
                        timestamp_str = f"[{dt.strftime('%d/%m %H:%M')}] "
                    except (ValueError, TypeError):
                        pass

            # Clean message content - single line
            raw_content = msg.content if msg.content else ""
            if not isinstance(raw_content, str):
                raw_content = str(raw_content)
            content = " ".join(raw_content.split())

            # Check message type
            # In V3, system messages can be tool results or summaries
            is_system = hasattr(msg, "type") and msg.type == "system"

            if is_system:
                if "📜 [RESUMO]" in content:
                    formatted.append(content)  # Already formatted summary line
                else:
                    formatted.append(f"{timestamp_str}⚙️ SISTEMA (Log): {content}")
            elif isinstance(msg, HumanMessage):
                formatted.append(f"{timestamp_str}🧑 Aluno: {content}")
            elif isinstance(msg, AIMessage):
                trainer_type = msg.additional_kwargs.get(
                    "trainer_type", current_trainer_type
                )
                if trainer_type == current_trainer_type:
                    formatted.append(f"{timestamp_str}🏋️ VOCÊ (Treinador): {content}")
                else:
                    formatted.append(
                        f"{timestamp_str}🏋️ EX-TREINADOR [{trainer_type}]: {content}"
                    )
            else:
                # Fallback for unknown message types
                formatted.append(f"{timestamp_str}> {content}")

        return "\n".join([str(item) for item in formatted])

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
                # Keep system messages as HumanMessage for visibility
                formatted_msgs.append(HumanMessage(content=content))

            elif isinstance(msg, HumanMessage):
                # Pass user messages as-is
                formatted_msgs.append(HumanMessage(content=content))

            elif isinstance(msg, AIMessage):
                # Pass AI messages as-is, preserving trainer_type in metadata if needed
                formatted_msgs.append(AIMessage(content=content, additional_kwargs=msg.additional_kwargs))
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

        # Parallelize profile retrieval
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_user = executor.submit(self._get_or_create_user_profile, user_email)
            future_trainer = executor.submit(
                self._get_or_create_trainer_profile, user_email
            )
            profile = future_user.result()
            trainer_profile_obj = future_trainer.result()

        # Retrieve Hybrid Memories
        hybrid_memories = self._retrieve_hybrid_memories(user_input, user_email)

        # Log memory retrieval statistics
        summary_length = len(profile.long_term_summary) if profile.long_term_summary else 0
        logger.info(
            "Memory retrieval for user %s: critical=%d, semantic=%d, recent=%d, summary_chars=%d",
            user_email,
            len(hybrid_memories["critical"]),
            len(hybrid_memories["semantic"]),
            len(hybrid_memories["recent"]),
            summary_length,
        )

        # Format memories into sections for the prompt
        # TODO: Move this formatting logic to Prompt Template in Phase 2
        memory_sections = []

        if hybrid_memories["critical"]:
            sec = ["## 🚨 Fatos Críticos (ATENÇÃO MÁXIMA):"]
            for mem in hybrid_memories["critical"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ⚠️ ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        if hybrid_memories["semantic"]:
            sec = ["## 🧠 Contexto Relacionado:"]
            for mem in hybrid_memories["semantic"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        if hybrid_memories["recent"]:
            sec = ["## 📅 Fatos Recentes:"]
            for mem in hybrid_memories["recent"]:
                dt = self._format_date(mem.get("created_at"))
                sec.append(f"- ({dt}) {mem['text']}")
            memory_sections.append("\n".join(sec))

        relevant_memories_str = (
            "\n\n".join(memory_sections)
            if memory_sections
            else "Nenhum conhecimento prévio relevante encontrado."
        )

        current_trainer_type = trainer_profile_obj.trainer_type or "atlas"

        # Get conversation memory with fixed window (V3 Strategy)
        # We rely on HistoryCompactor for long-term summarization, so we only need recent history here.
        conversation_memory = self._database.get_window_memory(
            session_id=user_email,
            k=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,  # Typically 20-40 matches
        )

        # Load memory variables (includes summary + recent messages if buffer exceeded)
        memory_vars = conversation_memory.load_memory_variables({})
        chat_history_messages = memory_vars.get("chat_history", [])

        # Format messages with trainer context
        chat_history_summary = self._format_memory_messages(
            chat_history_messages,
            current_trainer_type=current_trainer_type,
        )
        
        # New Structured History
        formatted_history_msgs = self._format_history_as_messages(
            chat_history_messages,
            current_trainer_type=current_trainer_type,
        )

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile_summary = profile.get_profile_summary()

        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile_summary,
            "user_profile_obj": profile,  # Passed for prompt template extraction
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary, # Kept for logging/compatibility or if template still uses it (we removed it)
            "chat_history": formatted_history_msgs,       # Passed to MessagesPlaceholder
            "user_message": user_input,
            "current_date": datetime.now().strftime("%Y-%m-%d"),  # Add current date for date calculations
        }

        prompt_template = self._get_prompt_template(input_data, is_telegram=is_telegram)

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

        # Create profile management tools
        from src.services.profile_tools import (
            create_get_user_goal_tool,
            create_update_user_goal_tool,
        )

        get_user_goal_tool = create_get_user_goal_tool(self._database, user_email)
        update_user_goal_tool = create_update_user_goal_tool(self._database, user_email)

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
            get_user_goal_tool,
            update_user_goal_tool,
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
            if isinstance(chunk, dict) and chunk.get("type") == "tool_result":
                tool_name = chunk.get("tool_name")
                content = chunk.get("content")
                # Create a concise log for the system
                log_msg = (
                    f"✅ Tool '{tool_name}' executed. Result: {str(content)[:200]}"
                )
                self._add_system_message_to_history(user_email, log_msg)
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

        if background_tasks:
            # Move DB saving to background to avoid blocking the generator completion
            background_tasks.add_task(
                self._add_to_mongo_history,
                user_email,
                user_input,
                final_response,
                current_trainer_type,
            )

            # We removed the restriction 'if not write_tool_was_called' because mixed messages
            # (e.g. "updated goal AND have allergy") were causing critical facts (allergy) to be lost.
            # Mem0 handles deduplication reasonably well, or we can refine later. Priority is capturing facts.
            background_tasks.add_task(
                _add_to_mem0_background,
                memory=self._memory,
                user_email=user_email,
                user_input=user_input,
                response_text=final_response,
            )

            # V3: Schedule History Compaction
            background_tasks.add_task(
                self.compactor.compact_history,
                user_email=user_email,
                active_window_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,  # Synced with window memory
                log_callback=log_callback,
            )

            logger.info(
                "Scheduled background tasks (Mongo + Mem0 + Compactor) for user: %s",
                user_email,
            )
        else:
            # Fallback for sync callers (like Telegram)
            self._add_to_mongo_history(
                user_email, user_input, final_response, current_trainer_type
            )

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
            # Create a dummy BackgroundTasks for the generator
            from fastapi import BackgroundTasks

            background_tasks = BackgroundTasks()

            async for chunk in self.send_message_ai(
                user_email=user_email,
                user_input=user_input,
                background_tasks=background_tasks,
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
                import nest_asyncio # type: ignore
                nest_asyncio.apply()
                return loop.run_until_complete(collect_response())
            return loop.run_until_complete(collect_response())


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

            memories = (
                result
                if isinstance(result, list)
                else result.get("memories", result.get("results", []))
            )
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

    def delete_memory(self, memory_id: str) -> bool:
        """
        Deletes a specific memory from Mem0.

        Args:
            memory_id (str): The unique ID of the memory to delete.

        Returns:
            bool: True if deletion was successful.
        """
        logger.info("Attempting to delete memory: %s", memory_id)
        try:
            self._memory.delete(memory_id=memory_id)
            logger.info("Successfully deleted memory: %s", memory_id)
            return True
        except Exception as e:
            logger.error("Failed to delete memory %s: %s", memory_id, e)
            raise

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        """
        Retrieves a specific memory by ID.

        Args:
            memory_id (str): The unique ID of the memory.

        Returns:
            dict | None: The memory object if found, otherwise None.
        """
        try:
            return self._memory.get(memory_id)
        except Exception as e:
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
