"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from datetime import datetime
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from mem0 import Memory

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.workout_tools import create_save_workout_tool, create_get_workouts_tool
from src.services.nutrition_tools import create_save_nutrition_tool, create_get_nutrition_tool
from src.core.logs import logger
from src.api.models.chat_history import ChatHistory
from src.api.models.user_profile import UserProfile
from src.api.models.sender import Sender
from src.api.models.trainer_profile import TrainerProfile


def _add_to_mem0_background(memory: Memory, user_email: str, user_input: str, response_text: str):
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
        logger.info("Successfully added conversation turn to Mem0 for user: %s", user_email)
    except Exception as e:
        # Log error but don't crash - Mem0 storage is not critical for user experience
        logger.error("Failed to add memory to Mem0 for user %s: %s", user_email, e)


class AITrainerBrain:
    """
    Service class responsible for orchestrating AI trainer interactions.
    Uses LLMClient for LLM operations (abstracted from specific providers).
    """

    def __init__(
        self, database: MongoDatabase, llm_client: LLMClient, memory: Memory
    ):
        self._database: MongoDatabase = database
        self._llm_client: LLMClient = llm_client
        self._memory: Memory = memory

    def _get_prompt_template(self, input_data: dict) -> ChatPromptTemplate:
        """Constructs and returns the chat prompt template."""
        logger.debug("Constructing chat prompt template.")
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", settings.PROMPT_TEMPLATE), ("human", "{user_message}")]
        )
        rendered_prompt = prompt_template.format(**input_data)
        
        # Multi-line formatted logging for better readability
        separator = "=" * 60
        logger.debug(
            "\n%s\n📤 PROMPT ENVIADO AO LLM\n%s\n%s\n%s",
            separator, separator, rendered_prompt, separator
        )
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
    
    def _retrieve_relevant_memories(
        self, user_input: str, user_id: str
    ) -> list[dict]:
        """
        Retrieves relevant memories for a given user input.

        Args:
            user_input (str): The user's input.
            user_id (str): The user's ID.

        Returns:
            list[dict]: A list of memory dicts with 'text' and 'created_at' keys.
        """
        logger.debug("Retrieving relevant memories for user: %s", user_id)
        # In Mem0 1.0.1+, search returns a dict: {"results": [...]}
        search_result = self._memory.search(
            user_id=user_id, 
            query=user_input,
            limit=settings.MAX_LONG_TERM_MEMORY_MESSAGES
        )
        
        # Normalize result to list of dictionaries
        memories_data = []
        if isinstance(search_result, dict):
            memories_data = search_result.get("results", [])
        elif isinstance(search_result, list):
            memories_data = search_result

        facts = []
        for mem in memories_data:
            text = mem.get("memory", "")
            created_at = mem.get("created_at", "")
            if text:
                logger.info("Retrieved fact from Mem0: %s (created: %s)", text, created_at)
                facts.append({"text": text, "created_at": created_at})
        
        return facts

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
            logger.info("User profile not found, creating default for user: %s", user_email)
            profile = UserProfile(
                email=user_email,
                gender="Masculino",
                age=30,
                weight=70.0,
                height=175,
                goal="Melhorar condicionamento",
                goal_type="maintain"
            )
            self.save_user_profile(profile)
        return profile

    def _get_or_create_trainer_profile(self, user_email: str) -> TrainerProfile:
        """Retrieves trainer profile or creates a default one if not found."""
        trainer_profile_obj = self._database.get_trainer_profile(user_email)
        if not trainer_profile_obj:
            logger.info("Trainer profile not found, creating default for user: %s", user_email)
            trainer_profile_obj = TrainerProfile(
                user_email=user_email,
                trainer_type="atlas"
            )
            self.save_trainer_profile(trainer_profile_obj)
        return trainer_profile_obj

    def _add_to_mongo_history(self, user_email: str, user_input: str, response_text: str, trainer_type: str):
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
            sender=Sender.STUDENT, text=user_input, timestamp=now, trainer_type=trainer_type
        )
        ai_message = ChatHistory(
            sender=Sender.TRAINER, text=response_text, timestamp=now, trainer_type=trainer_type
        )

        # Save to MongoDB (Session History) - synchronous
        self._database.add_to_history(user_message, user_email, trainer_type)
        self._database.add_to_history(ai_message, user_email, trainer_type)
        logger.info("Successfully saved conversation to MongoDB for user: %s (trainer: %s)", user_email, trainer_type)

    def _format_memory_messages(
        self,
        messages: list,
        current_trainer_type: str,
    ) -> str:
        """
        Formats LangChain messages with trainer context for the prompt.
        Handles both raw messages and summarized content from ConversationSummaryBufferMemory.
        
        Args:
            messages: List of LangChain messages (HumanMessage, AIMessage, or SystemMessage with summary)
            current_trainer_type: The active trainer type for context formatting
            
        Returns:
            Formatted string for the prompt
        """
        if not messages:
            return "No previous messages."
        
        formatted = []
        for msg in messages:
            # Check if it's a summary (SystemMessage with moving_summary_buffer content)
            if hasattr(msg, 'type') and msg.type == "system":
                formatted.append(f"📜 **[RESUMO DO HISTÓRICO]**\n> {msg.content}")
            elif isinstance(msg, HumanMessage):
                formatted.append(f"🧑 **Aluno**: {msg.content}")
            elif isinstance(msg, AIMessage):
                # Check trainer_type from additional_kwargs
                trainer_type = msg.additional_kwargs.get("trainer_type", current_trainer_type)
                if trainer_type == current_trainer_type:
                    formatted.append(f"🏋️ **Treinador**: {msg.content}")
                else:
                    formatted.append(
                        f"🏋️ **Treinador [PERFIL ANTERIOR: {trainer_type}]**:\n> [Contexto] {msg.content}"
                    )
            else:
                # Fallback for unknown message types
                formatted.append(f"> {msg.content}")
        
        return "\n\n---\n\n".join(formatted)

    def send_message_ai(self, user_email: str, user_input: str, background_tasks: BackgroundTasks = None):
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

        profile = self._get_or_create_user_profile(user_email)
        trainer_profile_obj = self._get_or_create_trainer_profile(user_email)

        relevant_memories = self._retrieve_relevant_memories(user_input, user_email)
        
        # Format facts as a bulleted list with dates for the prompt
        if relevant_memories:
            formatted_memories = []
            for mem in relevant_memories:
                try:
                    dt = datetime.fromisoformat(mem["created_at"].replace("Z", "+00:00"))
                    date_str = dt.strftime("%d/%m/%Y %H:%M")
                except (ValueError, KeyError, AttributeError):
                    date_str = "Data desconhecida"
                formatted_memories.append(f"- ({date_str}) {mem['text']}")
            relevant_memories_str = "\n".join(formatted_memories)
        else:
            relevant_memories_str = "Nenhum conhecimento prévio relevante encontrado."

        current_trainer_type = trainer_profile_obj.trainer_type or "atlas"
        
        # Get conversation memory with summarization support
        conversation_memory = self._database.get_conversation_memory(
            session_id=user_email,
            llm=self._llm_client._llm,  # Use same LLM for summarization
            max_token_limit=settings.SUMMARY_MAX_TOKEN_LIMIT,
        )
        
        # Load memory variables (includes summary + recent messages if buffer exceeded)
        memory_vars = conversation_memory.load_memory_variables({})
        chat_history_messages = memory_vars.get("chat_history", [])
        
        # Format messages with trainer context
        chat_history_summary = self._format_memory_messages(
            chat_history_messages,
            current_trainer_type=current_trainer_type,
        )

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile_summary = profile.get_profile_summary()

        # Metabolism Context Injection
        metabolism_context = "Dadox insuficientes para cálculo metabólico."
        try:
             from src.services.adaptive_tdee import AdaptiveTDEEService
             tdee_service = AdaptiveTDEEService(self._database)
             targets = tdee_service.get_current_targets(user_email)
             
             if targets.get("tdee"):
                 tdee = targets["tdee"]
                 target = targets["daily_target"]
                 reason = targets["reason"]
                 status = targets.get("status", "maintenance")
                 balance = targets.get("energy_balance", 0)
                 
                 metabolism_context = (
                     f"- **TDEE Estimado**: {tdee} kcal\n"
                     f"- **Meta Diária Recomendada**: {target} kcal\n"
                     f"- **Status Metabólico Atual**: {status} ({balance:+} kcal/dia)\n"
                     f"- **Justificativa**: {reason}\n"
                     f"> REGRAS CRÍTICAS:\n"
                     f"> 1. Se o status for 'deficit', o aluno ESTÁ PERDENDO peso.\n"
                     f"> 2. O TDEE é baseado na média histórica. PERGUNTE ao aluno se ele pretende manter a frequência de treinos nesta semana.\n"
                     f"> 3. Se ele for treinar MENOS que a média, sugira reduzir a meta (ex: -200kcal).\n"
                     f"> 4. Se ele for treinar MAIS, sugira aumentar levemente.\n"
                     f"> 5. Explique que o TDEE já inclui os treinos na média semanal."
                 )
        except Exception as e:
             logger.warning("Failed to inject metabolism context: %s", e)

        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile_summary,
            "relevant_memories": relevant_memories_str,
            "metabolism_context": metabolism_context,
            "chat_history_summary": chat_history_summary,
            "user_message": user_input,
        }

        prompt_template = self._get_prompt_template(input_data)
        
        # Create workout tracking tools with injected dependencies
        save_workout_tool = create_save_workout_tool(self._database, user_email)
        get_workouts_tool = create_get_workouts_tool(self._database, user_email)
        
        # Create nutrition tracking tools
        save_nutrition_tool = create_save_nutrition_tool(self._database, user_email)
        get_nutrition_tool = create_get_nutrition_tool(self._database, user_email)
        
        tools = [save_workout_tool, get_workouts_tool, save_nutrition_tool, get_nutrition_tool]
        
        full_response = []
        for chunk in self._llm_client.stream_with_tools(
            prompt_template=prompt_template, input_data=input_data, tools=tools
        ):
            full_response.append(chunk)
            yield chunk

        final_response = "".join(full_response)
        log_response = (final_response[:500] + "...") if len(final_response) > 500 else final_response
        logger.debug("LLM responded with: %s", log_response)

        # Save to MongoDB synchronously
        self._add_to_mongo_history(user_email, user_input, final_response, current_trainer_type)
        
        # Schedule Mem0 storage as background task (asynchronous)
        if background_tasks:
            background_tasks.add_task(
                _add_to_mem0_background,
                memory=self._memory,
                user_email=user_email,
                user_input=user_input,
                response_text=final_response
            )
            logger.info("Scheduled Mem0 background task for user: %s", user_email)

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

            memories = result if isinstance(result, list) else result.get("memories", result.get("results", []))
            logger.info("Retrieved %d memories from Mem0 for user: %s", len(memories), user_id)


            # Sort by created_at descending (newest first) and limit
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            limited_memories = memories[:limit]

            logger.debug("Returning %d memories after sorting and limiting", len(limited_memories))
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
        collection_name: str
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
            user_id, page, page_size
        )

        try:
            # Filter by user_id
            user_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id",
                        match=qdrant_models.MatchValue(value=user_id)
                    )
                ]
            )

            # Get total count for this user
            count_result = qdrant_client.count(
                collection_name=collection_name,
                count_filter=user_filter
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
                    with_payload=True
                )
                all_points.extend(points)
                if next_offset is None:
                    break

            # Sort by created_at descending (newest first)
            all_points.sort(
                key=lambda p: p.payload.get("created_at", "") if p.payload else "",
                reverse=True
            )

            # Apply pagination
            paginated_points = all_points[offset:offset + page_size]

            # Convert to memory dictionaries
            memories = []
            for point in paginated_points:
                payload = point.payload or {}
                memories.append({
                    "id": payload.get("id", str(point.id)),
                    "memory": payload.get("memory", payload.get("data", "")),
                    "created_at": payload.get("created_at"),
                    "updated_at": payload.get("updated_at"),
                })

            logger.info(
                "Returning %d memories for user %s (page %d of %d)",
                len(memories), user_id, page, (total + page_size - 1) // page_size
            )
            return memories, total

        except Exception as e:
            logger.error("Failed to retrieve paginated memories for user %s: %s", user_id, e)
            raise
