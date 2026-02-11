"""
This module contains the repository for chat history management using MongoDB.
"""

from datetime import datetime

from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import PromptTemplate
from langchain_classic.memory import (
    ConversationSummaryBufferMemory,
    ConversationBufferWindowMemory,
)

from src.core.config import settings
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.base import BaseRepository
from src.prompts.summary_prompts import SUMMARY_PROMPT


class ChatRepository(BaseRepository):
    """
    Repository for managing chat history using LangChain's MongoDB message history.
    """

    def __init__(self, database):
        super().__init__(database, "chat_history")

    def get_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[ChatHistory]:
        """
        Retrieves paginated chat history for a session.
        """
        self.logger.debug(
            "Retrieving chat history for session: %s (limit: %d, offset: %d)",
            user_id,
            limit,
            offset,
        )
        # Fetch enough messages to cover the offset from the end
        fetch_size = limit + offset
        history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=user_id,
            database_name=settings.DB_NAME,
            history_size=fetch_size,
        )
        messages = ChatHistory.from_mongodb_chat_message_history(history)

        if offset > 0:
            messages = messages[:-offset]

        if messages:
            messages = messages[-limit:]

        return messages

    def add_message(
        self,
        chat_history: ChatHistory,
        session_id: str,
        trainer_type: str | None = None,
    ):
        """
        Adds a message to the chat history.
        """
        self.logger.debug("Adding messages to chat history with timestamp.")
        now = datetime.now().isoformat()
        chat_history_mongo = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
        )

        additional_kwargs = {"timestamp": now}
        if trainer_type:
            additional_kwargs["trainer_type"] = trainer_type

        if chat_history.sender == Sender.TRAINER:
            chat_history_mongo.add_message(
                AIMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )
        elif chat_history.sender == Sender.SYSTEM:
            chat_history_mongo.add_message(
                SystemMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )
        else:
            chat_history_mongo.add_message(
                HumanMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )

    def get_memory_buffer(
        self,
        session_id: str,
        llm: BaseChatModel,
        max_token_limit: int | None = None,
    ) -> ConversationSummaryBufferMemory:
        """
        Returns a ConversationSummaryBufferMemory for a session.
        """
        if max_token_limit is None:
            max_token_limit = settings.SUMMARY_MAX_TOKEN_LIMIT

        chat_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )

        return ConversationSummaryBufferMemory(
            llm=llm,
            chat_memory=chat_history,
            max_token_limit=max_token_limit,
            return_messages=True,
            memory_key="chat_history",
            human_prefix="Aluno",
            ai_prefix="Treinador",
            prompt=PromptTemplate(
                input_variables=["summary", "new_lines"],
                template=SUMMARY_PROMPT.replace("{", "{{").replace("}", "}}")
                + "\n\nResumo atual:\n{summary}\n\nNovas linhas:\n{new_lines}\n\nNovo resumo:",
            ),
        )

    def get_window_memory(
        self,
        session_id: str,
        k: int = 40,
    ) -> ConversationBufferWindowMemory:
        """
        Returns a ConversationBufferWindowMemory that only looks at the last K messages.
        """
        chat_history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=k,
        )

        return ConversationBufferWindowMemory(
            chat_memory=chat_history,
            k=k,
            return_messages=True,
            memory_key="chat_history",
            human_prefix="Aluno",
            ai_prefix="Treinador",
        )

    # pylint: disable=unused-argument
    def get_unsummarized_messages(
        self, session_id: str, skip_last: int = 40
    ) -> list[dict]:
        """
        Retrieves messages that haven't been summarized yet. Currently returns empty list
        as V3 structure is pending.
        """
        return []
