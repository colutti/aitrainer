from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from .config import settings
from .database import MongoDatabase
from .logs import logger
from .models import ChatHistory, UserProfile
from mem0 import Memory
from langchain_google_genai import ChatGoogleGenerativeAI


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
        logger.debug("Final prompt sent to the LLM:\n%s", rendered_prompt)
        return prompt_template

    def _extract_conversation_text(self, messages: list) -> str:
        """
        Extracts raw text from messages with sender identification.

        Args:
            messages (list): List of message objects (HumanMessage/AIMessage).

        Returns:
            str: Formatted conversation text with sender labels.
        """
        messages_text = []
        for msg in messages:
            sender = "Student" if isinstance(msg, HumanMessage) else "Trainer"
            messages_text.append(f"{sender}: {msg.content}")
        return "\n".join(messages_text)

    def _call_llm_chain(self, prompt_template, input_data: dict) -> str:
        logger.info("Invoking LLM chain for user input: %s", input_data.get("input"))
        chain = prompt_template | self._llm | StrOutputParser()
        stream = chain.stream(input_data)
        chunks = []
        for chunk in stream:
            chunks.append(chunk)
        return "".join(chunks)

    def send_message_ai(self, profile: UserProfile, user_input: str, session_id) -> str:
        """
        Generates LLM response, summarizing history if needed.

        If the conversation history exceeds 20 messages, it will:
        1. Separate old messages (first 10) from recent messages (remaining)
        2. Summarize old messages and merge with existing summary
        3. Prune the chat history, keeping only recent messages
        4. Update the conversation summary in the database

        Args:
            profile (UserProfile): The user's profile.
            user_input (str): The user's input message.
            session_id (str): The chat session ID.

        Returns:
            str: The AI trainer's response.
        """
        logger.info("Generating workout stream for user: %s", profile.email)

        trainer_profile = self._database.get_trainer_profile(profile.email)
        if not trainer_profile:
            raise ValueError(f"Trainer profile not found for user: {profile.email}")

        chat_history = self._database.get_chat_history(session_id)
        relevant_memories = self._retrieve_relevant_memories(user_input, profile.email)

        trainer_profile = trainer_profile.get_trainer_profile_summary()
        user_profile = profile.get_profile_summary()

        # Format lists as strings for the prompt template
        relevant_memories_str = ChatHistory.format_as_string(
            relevant_memories, empty_message="Nenhuma memória relevante encontrada."
        )
        chat_history_summary = ChatHistory.format_as_string(
            chat_history, empty_message="Nenhuma mensagem anterior."
        )
        # Build input data and generate response
        input_data = {
            "trainer_profile": trainer_profile,
            "user_profile": user_profile,
            "relevant_memories": relevant_memories_str,
            "chat_history_summary": chat_history_summary,
            "user_message": user_input,
        }

        prompt_template = self._get_prompt_template(input_data)
        response_text = self._call_llm_chain(
            prompt_template=prompt_template, input_data=input_data
        )

        # self._add_to_history(chat_history, user_input, response_text)
        return response_text
