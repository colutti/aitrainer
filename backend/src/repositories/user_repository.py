"""
This module contains the repository for user profiles.
"""

from pymongo.database import Database
import bcrypt
from src.api.models.user_profile import UserProfile
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository for managing user profiles and authentication in MongoDB.
    """

    def __init__(self, database: Database):
        super().__init__(database, "users")

    def save_profile(self, profile: UserProfile) -> None:
        """
        Saves or updates a user profile.
        """
        # Exclude None values to prevent overwriting existing password_hash
        data = profile.model_dump(exclude_none=True)

        result = self.collection.update_one(
            {"email": profile.email}, {"$set": data}, upsert=True
        )
        if result.upserted_id:
            self.logger.info("New user profile created for email: %s", profile.email)
        elif result.modified_count > 0:
            self.logger.info("User profile updated for email: %s", profile.email)
        else:
            self.logger.debug(
                "User profile for email %s already up-to-date or no changes.",
                profile.email,
            )

    def update_profile_fields(self, email: str, fields: dict) -> bool:
        """
        Partially updates a user profile with specific fields.
        """
        result = self.collection.update_one({"email": email}, {"$set": fields})
        if result.modified_count > 0:
            self.logger.info("Partially updated user profile for email: %s", email)
            return True
        return False

    def get_profile(self, email: str) -> UserProfile | None:
        """
        Retrieves a user profile by email.
        """
        user_data = self.collection.find_one({"email": email})
        if not user_data:
            self.logger.info("User profile not found for email: %s", email)
            return None
        self.logger.debug("User profile retrieved for email: %s", email)
        return UserProfile(**user_data)

    def validate_credentials(self, email: str, password: str) -> bool:
        """
        Validates user credentials by checking the hashed password.
        """
        user = self.collection.find_one({"email": email})
        if not user:
            self.logger.debug("Login attempt for non-existent user: %s", email)
            return False
        password_hash = user.get("password_hash")
        if not password_hash or not password:
            self.logger.debug("Missing password or password hash for user: %s", email)
            return False

        try:
            if bcrypt.checkpw(password.encode(), password_hash.encode()):
                self.logger.debug("Successful password validation for user: %s", email)
                return True
        except (AttributeError, ValueError) as e:
            self.logger.error("Error during password validation for %s: %s", email, e)
            return False

        self.logger.debug("Failed password validation for user: %s", email)
        return False

    def find_by_webhook_token(self, token: str) -> UserProfile | None:
        """
        Finds a user by their Hevy webhook token.
        """
        # Ensure index exists (idempotent)
        self.collection.create_index("hevy_webhook_token", sparse=True)

        user_data = self.collection.find_one({"hevy_webhook_token": token})
        if not user_data:
            self.logger.debug("No user found for webhook token")
            return None
        self.logger.debug("Found user %s for webhook token", user_data.get("email"))
        return UserProfile(**user_data)
