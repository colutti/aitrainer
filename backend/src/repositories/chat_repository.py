"""
This module contains the repository for chat history management using MongoDB.
"""

import json
from datetime import datetime
from collections import namedtuple

from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    messages_from_dict,
)
from langchain_classic.memory import ConversationBufferWindowMemory

from src.core.config import settings
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.base import BaseRepository


class ChatRepository(BaseRepository):
    """
    Repository for managing chat history using LangChain's MongoDB message history.
    """

    def __init__(self, database):
        super().__init__(database, "message_store")
        self.db = database

    def get_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[ChatHistory]:
        """
        Retrieves paginated chat history for a session, excluding system messages.
        """
        self.logger.debug(
            "Retrieving chat history for session: %s (limit: %d, offset: %d)",
            user_id,
            limit,
            offset,
        )

        # 1. Query raw messages from MongoDB message_store
        # We fetch ALL and filter/sort in memory because message_store format is complex
        # and total number of messages per user is usually manageable (< 1000)
        cursor = self.collection.find({"SessionId": user_id})

        messages = []
        for doc in cursor:
            try:
                msg_dict = json.loads(doc["History"])
                msg_obj = messages_from_dict([msg_dict])[0]
                messages.append(msg_obj)
            except (json.JSONDecodeError, KeyError, IndexError):
                continue

        # 2. Convert to ChatHistory model (this also sorts them chronologically)
        _DummyHistory = namedtuple("_DummyHistory", ["messages"])
        all_chat_history = ChatHistory.from_mongodb_chat_message_history(
            _DummyHistory(messages)
        )

        # 3. Filter out SYSTEM messages before pagination
        public_messages = [
            msg for msg in all_chat_history if msg.sender != Sender.SYSTEM
        ]

        # 4. Apply pagination relative to the END (most recent messages)
        # Offset 0 means the last `limit` messages.
        # Offset 20 means the 21st to 40th most recent messages.
        if offset > 0:
            public_messages = public_messages[:-offset]

        if public_messages:
            public_messages = public_messages[-limit:]

        return public_messages

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
        if chat_history.images:
            additional_kwargs["images"] = chat_history.images

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
