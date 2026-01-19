"""
Repository for managing invite tokens in MongoDB.
"""
from datetime import datetime, timezone
from typing import Optional
from pymongo.database import Database

from src.api.models.invite import Invite
from src.repositories.base import BaseRepository


class InviteRepository(BaseRepository):
    """
    Repository for invite management with TTL index support.
    """

    def __init__(self, database: Database):
        super().__init__(database, "invites")
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        """
        Ensures required indexes exist on the invites collection.
        Creates TTL index on expires_at for automatic cleanup.
        """
        # TTL index for automatic deletion of expired invites
        self.collection.create_index("expires_at", expireAfterSeconds=0)
        # Unique index on token
        self.collection.create_index("token", unique=True)
        # Index on email for faster lookups
        self.collection.create_index("email")

    def create(self, invite: Invite) -> None:
        """
        Creates a new invite in the database.

        Args:
            invite: The Invite object to create.

        Raises:
            DuplicateKeyError: If token already exists.
        """
        self.collection.insert_one(invite.model_dump())
        self.logger.info("Created invite for email: %s, token: %s", invite.email, invite.token)

    def get_by_token(self, token: str) -> Optional[Invite]:
        """
        Retrieves an invite by its token.

        Args:
            token: The unique invite token.

        Returns:
            Invite object if found, None otherwise.
        """
        invite_data = self.collection.find_one({"token": token})
        if not invite_data:
            self.logger.debug("Invite not found for token: %s", token)
            return None
        return Invite(**invite_data)

    def get_by_email(self, email: str) -> Optional[Invite]:
        """
        Retrieves the most recent invite for an email.

        Args:
            email: The email address.

        Returns:
            Most recent Invite object if found, None otherwise.
        """
        invite_data = self.collection.find_one(
            {"email": email},
            sort=[("created_at", -1)]
        )
        if not invite_data:
            self.logger.debug("No invite found for email: %s", email)
            return None
        return Invite(**invite_data)

    def mark_as_used(self, token: str) -> bool:
        """
        Marks an invite as used.

        Args:
            token: The invite token to mark as used.

        Returns:
            True if invite was marked as used, False if not found.
        """
        result = self.collection.update_one(
            {"token": token},
            {
                "$set": {
                    "used": True,
                    "used_at": datetime.now(timezone.utc)
                }
            }
        )
        if result.modified_count > 0:
            self.logger.info("Marked invite as used: %s", token)
            return True
        self.logger.warning("Failed to mark invite as used (not found): %s", token)
        return False

    def revoke(self, token: str) -> bool:
        """
        Revokes (deletes) an invite.

        Args:
            token: The invite token to revoke.

        Returns:
            True if invite was deleted, False if not found.
        """
        result = self.collection.delete_one({"token": token})
        if result.deleted_count > 0:
            self.logger.info("Revoked invite: %s", token)
            return True
        self.logger.warning("Failed to revoke invite (not found): %s", token)
        return False

    def list_active(self) -> list[Invite]:
        """
        Lists all active (unused and not expired) invites.

        Returns:
            List of active Invite objects.
        """
        now = datetime.now(timezone.utc)
        invites_data = self.collection.find({
            "used": False,
            "expires_at": {"$gt": now}
        }).sort("created_at", -1)
        
        invites = [Invite(**data) for data in invites_data]
        self.logger.debug("Found %d active invites", len(invites))
        return invites

    def has_active_invite(self, email: str) -> bool:
        """
        Checks if an email has an active (unused, not expired) invite.

        Args:
            email: The email address to check.

        Returns:
            True if active invite exists, False otherwise.
        """
        now = datetime.now(timezone.utc)
        count = self.collection.count_documents({
            "email": email,
            "used": False,
            "expires_at": {"$gt": now}
        })
        return count > 0
