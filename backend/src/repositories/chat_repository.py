"""
This module contains the repository for chat history management using MongoDB.
"""

import json
from datetime import datetime

import pymongo
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
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
        self.ensure_indexes()

    _HISTORY_BATCH_SIZE_FACTOR = 3
    _MAX_HISTORY_BATCHES = 30

    def ensure_indexes(self) -> None:
        """Ensures indexes used by history pagination."""
        self.collection.create_index(
            [("SessionId", pymongo.ASCENDING), ("_id", pymongo.DESCENDING)],
            name="session_recent_history_idx",
        )
        self.logger.info("Chat history indexes ensured.")

    @staticmethod
    def _decode_public_chat_message(doc) -> ChatHistory | None:
        """
        Decodes a raw Mongo doc into ChatHistory and filters out system messages.
        """
        try:
            msg_dict = json.loads(doc["History"])
            msg_type = msg_dict.get("type")
            data = msg_dict.get("data", {})
            content = data.get("content", "")
            additional_kwargs = data.get("additional_kwargs", {}) or {}
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            return None

        if msg_type == "human":
            # Retroactive fix: some system messages were stored as human.
            if isinstance(content, str) and content.startswith("✅ Tool"):
                sender = Sender.SYSTEM
            else:
                sender = Sender.STUDENT
        elif msg_type == "system":
            sender = Sender.SYSTEM
        else:
            sender = Sender.TRAINER

        if sender == Sender.SYSTEM:
            return None

        return ChatHistory(
            text=content,
            translations=additional_kwargs.get("translations"),
            images=additional_kwargs.get("images"),
            sender=sender,
            timestamp=additional_kwargs.get("timestamp", datetime.min.isoformat()),
            trainer_type=additional_kwargs.get("trainer_type"),
        )

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

        # Query recent records in batches from the end of the collection
        # to avoid scanning the full conversation on every request.
        target_public = limit + max(offset, 0)
        batch_size = max(limit * self._HISTORY_BATCH_SIZE_FACTOR, limit)
        public_messages_desc = []
        oldest_seen_id = None

        for _ in range(self._MAX_HISTORY_BATCHES):
            query = {"SessionId": user_id}
            if oldest_seen_id is not None:
                query["_id"] = {"$lt": oldest_seen_id}
            cursor = (
                self.collection.find(query, {"History": 1})
                .sort("_id", -1)
                .limit(batch_size)
            )
            batch_docs = list(cursor)
            if not batch_docs:
                break
            oldest_seen_id = batch_docs[-1].get("_id")
            for doc in batch_docs:
                parsed = self._decode_public_chat_message(doc)
                if parsed is None:
                    continue
                public_messages_desc.append(parsed)
                if len(public_messages_desc) >= target_public:
                    break
            if len(public_messages_desc) >= target_public:
                break

        # Messages are collected as newest->oldest.
        # Apply offset/limit relative to the newest end, then reverse for UI chronology.
        if offset > 0:
            public_messages_desc = public_messages_desc[offset:]
        if limit > 0:
            public_messages_desc = public_messages_desc[:limit]

        public_messages_desc.reverse()
        return public_messages_desc

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
