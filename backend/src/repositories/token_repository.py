"""
This module contains the repository for token blocklist management.
"""

from datetime import datetime
from pymongo.database import Database
from src.repositories.base import BaseRepository


class TokenRepository(BaseRepository):
    """
    Repository for managing blocked JWT tokens in MongoDB with TTL.
    """

    def __init__(self, database: Database):
        super().__init__(database, "token_blocklist")

    def add_to_blocklist(self, token: str, expires_at: datetime) -> None:
        """
        Adds a token to the blocklist with an expiration time.
        """
        self.collection.update_one(
            {"token": token},
            {"$set": {"token": token, "expires_at": expires_at}},
            upsert=True,
        )
        self.logger.debug("Token added to blocklist.")

    def is_blocklisted(self, token: str) -> bool:
        """
        Checks if a token is in the blocklist.
        """
        result = self.collection.find_one({"token": token})
        return result is not None

    def ensure_indexes(self) -> None:
        """
        Ensures a TTL index on the expires_at field.
        """
        self.collection.create_index("expires_at", expireAfterSeconds=0)
        self.logger.info("Blocklist TTL index ensured.")
