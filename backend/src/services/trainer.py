"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from datetime import datetime
from fastapi import BackgroundTasks
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from mem0 import Memory
import google.api_core.exceptions

from src.core.config import settings
from src.services.database import MongoDatabase
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
    Service class responsible for interacting with the LLM (Gemini).
    """

    def __init__(
        self, database: MongoDatabase, llm: ChatGoogleGenerativeAI, memory: Memory
    ):
        self._database = database
        self._llm = llm
        self._memory = memory

    def _get_prompt_template(self, input_data: dict) -> ChatPromptTemplate:
        """Constructs and returns the chat prompt template."""
        logger.debug("Constructing chat prompt template.")
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", settings.PROMPT_TEMPLATE), ("human", "{user_message}")]
        )
        rendered_prompt = prompt_template.format(**input_data)
        log_prompt = (rendered_prompt[:500] + "...") if len(rendered_prompt) > 500 else rendered_prompt
        logger.debug("Final prompt sent to the LLM:\n%s", log_prompt)
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

    def _call_llm_chain(self, prompt_template, input_data: dict):
        """
        Invokes the LLM chain and yields response chunks as they arrive.
        
        Args:
            prompt_template: The prompt template to use.
            input_data (dict): The input data for the chain.
            
        Yields:
            str: Individual chunks of the LLM response.
        """
        logger.info("Invoking LLM chain for user input: %s", input_data.get("user_message"))
        chain = prompt_template | self._llm | StrOutputParser()
        try:
            stream = chain.stream(input_data)
            for chunk in stream:
                yield chunk
        except google.api_core.exceptions.ResourceExhausted as e:
            logger.error("Gemini API Quota Exceeded: %s", e)
            yield "There was a problem accessing the Gemini API. Please try again later or check your quota."
        except Exception as e:
            logger.error("An unexpected error occurred during LLM chain invocation: %s", e)
            yield "An unexpected error occurred while processing your request. Please try again later."

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
    ) -> list[str]:
        """
        Retrieves relevant memories for a given user input.

        Args:
            user_input (str): The user's input.
            user_id (str): The user's ID.

        Returns:
            list[str]: A list of relevant facts (strings).
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
            if text:
                logger.info("Retrieved fact from Mem0: %s", text)
                facts.append(text)
        
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
        
        # Format facts as a bulleted list for the prompt
        if relevant_memories:
            relevant_memories_str = "\n".join([f"- {fact}" for fact in relevant_memories])
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
        
        full_response = []
        for chunk in self._call_llm_chain(
            prompt_template=prompt_template, input_data=input_data
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


