"""Repository for Telegram integration data."""

import secrets
import string
from datetime import datetime, timezone, timedelta
from typing import Optional

from pymongo.database import Database

from src.repositories.base import BaseRepository
from src.api.models.telegram_link import TelegramLink


class TelegramRepository(BaseRepository):
    """Repository for managing Telegram links and codes."""

    def __init__(self, database: Database):
        super().__init__(database, "telegram_links")
        self.codes_collection = database["telegram_codes"]
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """Create necessary indexes."""
        # TTL index for automatic code expiration
        self.codes_collection.create_index("expires_at", expireAfterSeconds=0)
        # Unique index on chat_id
        self.collection.create_index("chat_id", unique=True, sparse=True)
        # Index on user_email for quick lookups
        self.collection.create_index("user_email", sparse=True)

    def create_linking_code(self, user_email: str) -> str:
        """
        Generate a 6-character linking code.
        Deletes any existing codes for this user first.
        """
        # Delete existing codes for this user
        self.codes_collection.delete_many({"user_email": user_email})

        # Generate new code
        alphabet = string.ascii_uppercase + string.digits
        code = "".join(secrets.choice(alphabet) for _ in range(6))

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=10)

        self.codes_collection.insert_one(
            {
                "code": code,
                "user_email": user_email,
                "created_at": now,
                "expires_at": expires_at,
            }
        )

        self.logger.info("Created linking code for %s", user_email)
        return code

    def validate_and_consume_code(
        self, code: str, chat_id: int, username: Optional[str] = None
    ) -> Optional[str]:
        """
        Validate code and create link if valid.
        Returns user_email if successful, None otherwise.
        """
        # Find and delete code atomically
        code_doc = self.codes_collection.find_one_and_delete({"code": code.upper()})

        if not code_doc:
            self.logger.warning("Invalid or expired code: %s", code)
            return None

        user_email = code_doc["user_email"]

        # Delete any existing link for this user or chat_id
        self.collection.delete_many(
            {"$or": [{"user_email": user_email}, {"chat_id": chat_id}]}
        )

        # Create new link
        self.collection.insert_one(
            {
                "chat_id": chat_id,
                "user_email": user_email,
                "telegram_username": username,
                "linked_at": datetime.now(timezone.utc),
            }
        )

        self.logger.info("Linked %s to chat_id %s", user_email, chat_id)
        return user_email

    def get_link_by_chat_id(self, chat_id: int) -> Optional[TelegramLink]:
        """Find link by Telegram chat ID."""
        doc = self.collection.find_one({"chat_id": chat_id})
        if not doc:
            return None
        return TelegramLink(**doc)

    def get_link_by_email(self, email: str) -> Optional[TelegramLink]:
        """Find link by user email."""
        doc = self.collection.find_one({"user_email": email})
        if not doc:
            return None
        return TelegramLink(**doc)

    def delete_link(self, user_email: str) -> bool:
        """Delete link for user."""
        result = self.collection.delete_one({"user_email": user_email})
        if result.deleted_count > 0:
            self.logger.info("Deleted Telegram link for %s", user_email)
            return True
        return False
