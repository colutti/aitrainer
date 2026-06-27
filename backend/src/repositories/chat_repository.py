"""
This module contains the repository for chat history management using MongoDB.
"""

import json
from datetime import datetime

import pymongo
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.base import BaseRepository


class SimpleWindowMemory:  # pylint: disable=too-few-public-methods
    """Small compatibility wrapper for callers expecting load_memory_variables."""

    def __init__(self, messages: list[ChatHistory]):
        self.messages = messages

    def load_memory_variables(self, _inputs):
        """Return history using the old memory-variable shape."""
        return {"chat_history": self.messages}


class ChatRepository(BaseRepository):
    """
    Repository for managing public chat history in MongoDB.
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
            raw_history = doc["History"]
            msg_dict = (
                json.loads(raw_history) if isinstance(raw_history, str) else raw_history
            )
            msg_type = msg_dict.get("type") or msg_dict.get("sender")
            data = msg_dict.get("data", {})
            if not isinstance(data, dict):
                data = {}
            content = data.get("content", msg_dict.get("text", ""))
            additional_kwargs = data.get("additional_kwargs", {}) or {}
            timestamp = (
                additional_kwargs.get("timestamp")
                or msg_dict.get("timestamp")
                or datetime.min.isoformat()
            )
            translations = additional_kwargs.get("translations") or msg_dict.get(
                "translations"
            )
            images = additional_kwargs.get("images") or msg_dict.get("images")
            trainer_type = additional_kwargs.get("trainer_type") or msg_dict.get(
                "trainer_type"
            )
        except (json.JSONDecodeError, KeyError, AttributeError, TypeError):
            return None

        if msg_type in {"human", Sender.STUDENT.value, "student"}:
            # Retroactive fix: some system messages were stored as human.
            if isinstance(content, str) and content.startswith("✅ Tool"):
                sender = Sender.SYSTEM
            else:
                sender = Sender.STUDENT
        elif msg_type in {"system", Sender.SYSTEM.value}:
            sender = Sender.SYSTEM
        else:
            sender = Sender.TRAINER

        if sender == Sender.SYSTEM:
            return None

        return ChatHistory(
            text=content,
            translations=translations,
            images=images,
            sender=sender,
            timestamp=timestamp,
            trainer_type=trainer_type,
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
        now = datetime.now().isoformat()
        self.add_messages(
            [
                chat_history.model_copy(
                    update={"timestamp": chat_history.timestamp or now}
                )
            ],
            session_id,
            trainer_type,
        )

    def add_messages(
        self,
        chat_histories: list[ChatHistory],
        session_id: str,
        trainer_type: str | None = None,
    ) -> None:
        """Persist multiple chat messages with one MongoDB round trip."""
        now = datetime.now().isoformat()
        documents = []
        for chat_history in chat_histories:
            additional_kwargs = {"timestamp": now}
            if trainer_type:
                additional_kwargs["trainer_type"] = trainer_type
            if chat_history.images:
                additional_kwargs["images"] = chat_history.images

            documents.append(
                {
                    "SessionId": session_id,
                    "History": {
                        "sender": chat_history.sender.value,
                        "text": chat_history.text,
                        "timestamp": additional_kwargs["timestamp"],
                        "images": chat_history.images,
                        "trainer_type": trainer_type,
                        "translations": chat_history.translations,
                    },
                }
            )

        if documents:
            self.collection.insert_many(documents, ordered=True)

    def get_window_memory(self, session_id: str, k: int = 40) -> SimpleWindowMemory:
        """Return a compatibility object containing the latest public messages."""
        return SimpleWindowMemory(self.get_history(session_id, limit=k, offset=0))

    def get_pydantic_ai_history(self, session_id: str, limit: int = 20) -> list:
        """Return recent public history as Pydantic AI model messages."""
        messages = self.get_history(session_id, limit=limit, offset=0)
        result = []
        for message in messages:
            try:
                timestamp = datetime.fromisoformat(message.timestamp)
            except (ValueError, TypeError):
                timestamp = datetime.now()
            if message.sender == Sender.STUDENT:
                result.append(
                    ModelRequest(
                        parts=[UserPromptPart(content=message.text, timestamp=timestamp)],
                        timestamp=timestamp,
                    )
                )
            elif message.sender == Sender.TRAINER:
                result.append(
                    ModelResponse(
                        parts=[TextPart(content=message.text)],
                        timestamp=timestamp,
                        model_name=message.trainer_type,
                    )
                )
        return result
