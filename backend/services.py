from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBChatMessageHistory

from .config import settings
from .database import (get_conversation_summary, get_trainer_profile,
                       save_conversation_summary)
from .logs import logger
from .models import ConversationSummary, UserProfile
from .prompt_template import SUMMARY_INITIAL_TEMPLATE, SUMMARY_MERGE_TEMPLATE


class AITrainerBrain:
    """
    Service class responsible for interacting with the LLM (Gemini).
    """
    MAX_MESSAGES = 50

    def get_chat_history(self, session_id: str) -> list[dict]:
        """
        Retorna o histórico de chat formatado para o frontend, incluindo timestamp.
        """
        history = self._get_chat_history(session_id)
        formatted = []
        for msg in history.messages:
            ts = None
            if hasattr(msg, "additional_kwargs"):
                ts = msg.additional_kwargs.get("timestamp")
            formatted.append({
                "text": msg.content,
                "sender": "user" if isinstance(msg, HumanMessage) else "ai",
                "timestamp": ts if ts else None
            })

        def parse_ts(ts):
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                return datetime.now()

        formatted.sort(key=lambda m: parse_ts(m["timestamp"]) if m["timestamp"] else datetime.now())
        return formatted

    def _get_llm(self):
        logger.info("Instantiating Gemini LLM with model: %s", settings.MODEL_NAME)

        # Troque 'api_key' para SecretStr se necessário
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GEMINI_API_KEY or "",
            temperature=0.7
        )

    def _get_summary_llm(self):
        """
        Returns an LLM instance configured for generating conversation summaries.

        Uses a cheaper model (configured via SUMMARY_MODEL_NAME) to reduce costs
        when generating summaries. Lower temperature for more consistent summaries.

        Returns:
            ChatGoogleGenerativeAI: An LLM instance for summary generation.
        """
        model_name = getattr(settings, "SUMMARY_MODEL_NAME", settings.MODEL_NAME)
        logger.info("Instantiating Gemini LLM for summaries with model: %s", model_name)
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY or "",
            temperature=0.3
        )

    def __init__(self) -> None:
        """Initializes the AITrainerBrain service."""
        logger.info("AITrainerBrain service initialized.")
        self.max_messages = self.MAX_MESSAGES

    def set_max_messages(self, n: int):
        """Allows configuring how many recent messages to keep in context."""
        logger.info("Setting max_messages to %d", n)
        self.max_messages = n

    def _get_chat_history(self, session_id: str) -> MongoDBChatMessageHistory:
        """Retrieves chat history from MongoDB for the given session ID."""
        logger.debug("Retrieving chat history for session: %s", session_id)
        return MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=self.max_messages
        )

    def _get_prompt_template(self, input_data: dict) -> ChatPromptTemplate:
        """Constructs and returns the chat prompt template."""
        logger.debug("Constructing chat prompt template.")
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", settings.PROMPT_TEMPLATE),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{user_message}")
        ])
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

    def _summarize_old_messages(self, current_summary: str, messages: list) -> str:
        """
        Summarizes old messages by merging them with the current summary.

        Extracts raw text from messages, identifies sender (Student or Trainer),
        and uses the summary LLM to generate a concise updated summary.

        Args:
            current_summary (str): The existing conversation summary. Empty string if first time.
            messages (list): List of message objects (HumanMessage/AIMessage) to summarize.

        Returns:
            str: A new concise summary that merges the current summary with the messages.
        """
        try:
            conversation_text = self._extract_conversation_text(messages)

            # Build input data for summary prompt
            if not current_summary or current_summary.strip() == "":
                input_data = {"conversation_text": conversation_text}
                prompt_template = ChatPromptTemplate.from_template(SUMMARY_INITIAL_TEMPLATE)
            else:
                input_data = {
                    "current_summary": current_summary,
                    "conversation_text": conversation_text
                }
                prompt_template = ChatPromptTemplate.from_template(SUMMARY_MERGE_TEMPLATE)

            # Use summary LLM (cheaper model) via _call_llm_chain
            new_summary = self._call_llm_chain(
                prompt_template=prompt_template,
                input_data=input_data
            )

            logger.info("Successfully generated conversation summary")
            return new_summary.strip()

        except (ValueError, AttributeError) as e:
            logger.error("Error generating summary: %s", str(e))
            # Return current summary if summarization fails
            return current_summary

    def _prune_history(
        self, chat_history: MongoDBChatMessageHistory, recent_messages: list
    ) -> None:
        """
        Prunes chat history by clearing it and re-adding only recent messages with preserved timestamps.

        Args:
            chat_history (MongoDBChatMessageHistory): The chat history object to prune.
            recent_messages (list): List of recent message objects to keep.
        """
        chat_history.clear()
        for msg in recent_messages:
            timestamp = None
            if hasattr(msg, "additional_kwargs"):
                timestamp = msg.additional_kwargs.get("timestamp")

            if isinstance(msg, HumanMessage):
                chat_history.add_message(
                    HumanMessage(
                        content=msg.content,
                        additional_kwargs={"timestamp": timestamp} if timestamp else {}
                    )
                )
            elif isinstance(msg, AIMessage):
                chat_history.add_message(
                    AIMessage(
                        content=msg.content,
                        additional_kwargs={"timestamp": timestamp} if timestamp else {}
                    )
                )

    def _update_conversation_summary(self, user_email: str, summary: str) -> None:
        """
        Updates the conversation summary in the database.

        Args:
            user_email (str): The user's email address.
            summary (str): The new summary text.
        """
        updated_summary = ConversationSummary(
            user_email=user_email,
            summary=summary
        )
        save_conversation_summary(updated_summary)

    def _maybe_summarize_and_prune_history(
        self,
        chat_history: MongoDBChatMessageHistory,
        user_email: str,
        current_summary: str,
        message_limit: int = 20,
        messages_to_summarize: int = 10,
    ) -> str:
        """
        Summarizes old messages and prunes history if message count exceeds limit.

        Args:
            chat_history (MongoDBChatMessageHistory): The chat history object.
            user_email (str): The user's email address.
            current_summary (str): The current conversation summary.
            message_limit (int): Maximum number of messages before summarization (default: 20).
            messages_to_summarize (int): Number of old messages to summarize (default: 10).

        Returns:
            str: Updated summary (or current summary if no summarization occurred).
        """
        messages = chat_history.messages

        if len(messages) <= message_limit:
            return current_summary

        logger.info(
            "History exceeds limit (%d > %d). Summarizing old messages.",
            len(messages),
            message_limit
        )

        # Separate old messages from recent ones
        old_messages = messages[:messages_to_summarize]
        recent_messages = messages[messages_to_summarize:]

        # Generate new summary by merging current summary with old messages
        new_summary = self._summarize_old_messages(current_summary, old_messages)

        # Update conversation summary in database
        self._update_conversation_summary(user_email, new_summary)

        # Prune history: clear and re-add only recent messages
        self._prune_history(chat_history, recent_messages)

        logger.info("History pruned. Kept %d recent messages.", len(recent_messages))
        return new_summary

    def _add_to_history(self, chat_history: MongoDBChatMessageHistory, user_input: str, ai_response: str):
        """Adds user and AI messages to the chat history, with timestamp."""
        logger.debug("Adding messages to chat history with timestamp.")
        now = datetime.now().isoformat()
        chat_history.add_message(
            HumanMessage(
                content=user_input,
                additional_kwargs={"timestamp": now}
            )
        )
        chat_history.add_message(
            AIMessage(
                content=ai_response,
                additional_kwargs={"timestamp": now}
            )
        )

    def _call_llm_chain(self, prompt_template, input_data: dict) -> str:
        logger.info("Invoking LLM chain for user input: %s", input_data.get("input"))
        llm = self._get_llm()
        chain = prompt_template | llm | StrOutputParser()
        stream = chain.stream(input_data)
        chunks = []
        for chunk in stream:
            chunks.append(chunk)
        return ''.join(chunks)


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

        trainer_profile = get_trainer_profile(profile.email)
        if not trainer_profile:
            raise ValueError(f"Trainer profile not found for user: {profile.email}")

        chat_history = self._get_chat_history(session_id)
        conversation_summary = get_conversation_summary(profile.email)
        current_summary = conversation_summary.summary if conversation_summary else ""
        current_summary = self._maybe_summarize_and_prune_history(
            chat_history, profile.email, current_summary
        )

        trainer_profile = trainer_profile.get_trainer_profile_summary()
        user_profile = profile.get_profile_summary()

        # Build input data and generate response
        input_data = {
            **profile.model_dump(),
            "trainer_profile": trainer_profile,
            "user_profile": user_profile,
            "summary": current_summary,
            "chat_history": chat_history.messages,
            "user_message": user_input
        }

        prompt_template = self._get_prompt_template(input_data)
        response_text = self._call_llm_chain(
            prompt_template=prompt_template,
            input_data=input_data
        )

        self._add_to_history(chat_history, user_input, response_text)
        return response_text
