"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from datetime import datetime
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from mem0 import Memory

from src.core.config import settings
from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.services.workout_tools import create_save_workout_tool, create_get_workouts_tool
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

    def _extract_conversation_text(self, messages: list) -> str:
        """
        Extracts raw text from messages with sender identification.

        Args:
            messages (list): List of message objects (HumanMessage/AIMessage).

        Returns:
            str: Formatted conversation text with sender labels.
        """
        logger.debug("Extracting conversation text from %d messages.", len(messages))
        messages_text = []
        for msg in messages:
            sender = "Student" if isinstance(msg, HumanMessage) else "Trainer"
            messages_text.append(f"{sender}: {msg.content}")
        return "\n".join(messages_text)

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
        search_result = self._memory.search(user_id=user_id, query=user_input)
        
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

    def _add_to_mongo_history(self, user_email: str, user_input: str, response_text: str):
        """
        Adds the user input and AI response to MongoDB chat history (synchronous).
        
        Args:
            user_email (str): The user's email.
            user_input (str): The user's input message.
            response_text (str): The AI's response message.
        """
        now = datetime.now().isoformat()
        user_message = ChatHistory(
            sender=Sender.STUDENT, text=user_input, timestamp=now
        )
        ai_message = ChatHistory(
            sender=Sender.TRAINER, text=response_text, timestamp=now
        )

        # Save to MongoDB (Session History) - synchronous
        self._database.add_to_history(user_message, user_email)
        self._database.add_to_history(ai_message, user_email)
        logger.info("Successfully saved conversation to MongoDB for user: %s", user_email)

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

        profile = self.get_user_profile(user_email)
        if not profile:
            logger.warning("User profile not found for email: %s", user_email)
            raise ValueError(f"User profile not found for email: {user_email}")

        trainer_profile_obj = self._database.get_trainer_profile(user_email)
        if not trainer_profile_obj:
            logger.warning("Trainer profile not found for user: %s", user_email)
            raise ValueError(f"Trainer profile not found for user: {user_email}")

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

        chat_history = self._database.get_chat_history(user_email)
        chat_history_summary = ChatHistory.format_as_string(
            chat_history, empty_message="No previous messages."
        )

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile_summary = profile.get_profile_summary()

        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile_summary,
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary,
            "user_message": user_input,
        }

        prompt_template = self._get_prompt_template(input_data)
        
        # Create workout tracking tools with injected dependencies
        save_workout_tool = create_save_workout_tool(self._database, user_email)
        get_workouts_tool = create_get_workouts_tool(self._database, user_email)
        tools = [save_workout_tool, get_workouts_tool]
        
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
        self._add_to_mongo_history(user_email, user_input, final_response)
        
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


