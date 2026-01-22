from pymongo.database import Database
import bcrypt
from src.api.models.user_profile import UserProfile
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, database: Database):
        super().__init__(database, "users")

    def save_profile(self, profile: UserProfile) -> None:
        result = self.collection.update_one(
            {"email": profile.email}, {"$set": profile.model_dump()}, upsert=True
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

    def get_profile(self, email: str) -> UserProfile | None:
        user_data = self.collection.find_one({"email": email})
        if not user_data:
            self.logger.info("User profile not found for email: %s", email)
            return None
        self.logger.debug("User profile retrieved for email: %s", email)
        return UserProfile(**user_data)

    def validate_credentials(self, email: str, password: str) -> bool:
        user = self.collection.find_one({"email": email})
        if not user:
            self.logger.debug("Login attempt for non-existent user: %s", email)
            return False
        password_hash = user.get("password_hash", "")
        if bcrypt.checkpw(password.encode(), password_hash.encode()):
            self.logger.debug("Successful password validation for user: %s", email)
            return True
        self.logger.debug("Failed password validation for user: %s", email)
        return False

    def find_by_webhook_token(self, token: str) -> UserProfile | None:
        """
        Finds a user by their Hevy webhook token.
        Ensures a sparse index exists on the token field.

        Args:
            token: The unique webhook token.

        Returns:
            UserProfile if found, None otherwise.
        """
        # Ensure index exists (idempotent)
        self.collection.create_index("hevy_webhook_token", sparse=True)

        user_data = self.collection.find_one({"hevy_webhook_token": token})
        if not user_data:
            self.logger.debug("No user found for webhook token")
            return None
        self.logger.debug("Found user %s for webhook token", user_data.get("email"))
        return UserProfile(**user_data)
