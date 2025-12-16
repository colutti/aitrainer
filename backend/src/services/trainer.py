"""
This module contains the AI trainer brain, which is responsible for interacting with the LLM.
"""

from datetime import datetime
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

    def _call_llm_chain(self, prompt_template, input_data: dict) -> str:
        logger.info("Invoking LLM chain for user input: %s", input_data.get("input"))
        chain = prompt_template | self._llm | StrOutputParser()
        try:
            stream = chain.stream(input_data)
            chunks = []
            for chunk in stream:
                chunks.append(chunk)
            return "".join(chunks)
        except google.api_core.exceptions.ResourceExhausted as e:
            logger.error("Gemini API Quota Exceeded: %s", e)
            return "There was a problem accessing the Gemini API. Please try again later or check your quota."

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
    ) -> list[ChatHistory]:
        """
        Retrieves relevant memories for a given user input.

        Args:
            user_input (str): The user's input.
            user_id (str): The user's ID.

        Returns:
            list[ChatHistory]: A list of relevant memories.
        """
        logger.debug("Retrieving relevant memories for user: %s", user_id)
        memories = self._memory.search(user_id=user_id, query=user_input)

        chat_histories = []
        for mem_data in memories:  # mem_data is a string, original timestamp is not available
            chat_histories.append(
                ChatHistory(
                    text=mem_data,  # Use the string directly as the text content
                    sender=Sender.TRAINER, # Keep the default sender
                    timestamp=datetime.now().isoformat(), # Generate a current timestamp
                )
            )
        return chat_histories

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

    def _add_to_history(self, user_email: str, user_input: str, response_text: str):
        """
        Adds the user input and AI response to the chat history.
        """
        now = datetime.now().isoformat()
        user_message = ChatHistory(
            sender=Sender.STUDENT, text=user_input, timestamp=now
        )
        ai_message = ChatHistory(
            sender=Sender.TRAINER, text=response_text, timestamp=now
        )

        self._database.add_to_history(user_message, user_email)
        self._database.add_to_history(ai_message, user_email)

    def send_message_ai(self, user_email: str, user_input: str) -> str:
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

        Returns:
            str: The AI trainer's response.
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

        chat_history = self._database.get_chat_history(user_email)
        relevant_memories = self._retrieve_relevant_memories(user_input, user_email)

        trainer_profile_summary = trainer_profile_obj.get_trainer_profile_summary()
        user_profile = profile.get_profile_summary()

        # Format lists as strings for the prompt template
        relevant_memories_str = ChatHistory.format_as_string(
            relevant_memories, empty_message="No relevant memories found."
        )
        chat_history_summary = ChatHistory.format_as_string(
            chat_history, empty_message="No previous messages."
        )
        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile_summary,
            "user_profile": user_profile,
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary,
            "user_message": user_input,
        }

        prompt_template = self._get_prompt_template(input_data)
        response_text = self._call_llm_chain(
            prompt_template=prompt_template, input_data=input_data
        )
        log_response = (response_text[:500] + "...") if len(response_text) > 500 else response_text
        logger.debug("LLM responded with: %s", log_response)

        self._add_to_history(user_email, user_input, response_text)
        return response_text

