from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mongodb import MongoDBChatMessageHistory

from .config import settings
from .database import get_trainer_profile
from .logs import logger
from .models import UserProfile


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
            ("human", "{input}")
        ])
        rendered_prompt = prompt_template.format(**input_data)
        logger.debug("Final prompt sent to the LLM:\n%s", rendered_prompt)
        return prompt_template

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
        """
        logger.info("Generating workout stream for user: %s", profile.email)
        chat_history = self._get_chat_history(session_id)
        trainer_profile = get_trainer_profile(profile.email)
        if not trainer_profile:
            raise ValueError(f"Trainer profile not found for user: {profile.email}")

        input_data = {
            **profile.model_dump(),
            **(trainer_profile.model_dump()),
            "chat_history": chat_history.messages,
            "input": user_input
        }
        prompt_template = self._get_prompt_template(input_data)
        response_text = self._call_llm_chain(
            prompt_template=prompt_template,
            input_data=input_data
        )
        self._add_to_history(chat_history, user_input, response_text)
        return response_text
