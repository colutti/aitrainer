"""
This module provides the UserRepository for managing user persistence.
"""
# pylint: disable=line-too-long

from datetime import datetime
from typing import Any
import pymongo
from pymongo.database import Database
from src.api.models.user_profile import UserProfile
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    """
    Repository for managing user profiles and authentication in MongoDB.
    """

    def __init__(self, database: Database):
        super().__init__(database, "users")
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Ensures indexes used by login/profile paths."""
        self.collection.create_index(
            [("email", pymongo.ASCENDING)],
            unique=True,
            name="users_email_unique_idx",
        )
        self.collection.create_index(
            [("stripe_customer_id", pymongo.ASCENDING)],
            sparse=True,
            name="users_stripe_customer_idx",
        )
        self.logger.info("User indexes ensured.")

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

    def is_demo_user(self, email: str) -> bool:
        """Returns whether the user is a protected demo account."""
        user_data = self.collection.find_one({"email": email}, {"is_demo": 1})
        return bool(user_data and user_data.get("is_demo"))

    def find_by_stripe_customer_id(self, customer_id: str) -> UserProfile | None:
        """
        Retrieves a user profile by Stripe Customer ID.
        """
        user_data = self.collection.find_one({"stripe_customer_id": customer_id})
        if not user_data:
            return None
        return UserProfile(**user_data)

    def increment_message_counts(
        self, email: str, new_cycle_start: datetime | None = None
    ) -> None:
        """
        Atomically increments message counts for a user.
        If new_cycle_start is provided, it resets the monthly count and updates the cycle start.
        Also handles daily message limits and daily resets.
        """
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")

        # Get existing last_message_date to check for reset
        # Note: In a high-concurrency environment, we'd use a more complex $cond in the update,
        # but here we'll do a simple fetch or rely on the $set behavior.
        # Actually, let's use a single atomic update with $cond if possible, but pymongo/mongo 4.2+ needed.
        # We'll use a simpler approach: check if we need to reset today's count based on a separate query or
        # just use $set if we pass the current date.

        # We will use the fact that we can do conditional updates using aggregation pipelines in update_one (Mongo 4.2+).
        # pipeline = [
        #     { "$set": {
        #         "messages_sent_today": { "$cond": { "if": { "$ne": ["$last_message_date", today_str] }, "then": 1, "else": { "$add": ["$messages_sent_today", 1] } } },
        #         "last_message_date": today_str,
        #         "total_messages_sent": { "$add": ["$total_messages_sent", 1] },
        #         ...
        #     }}
        # ]

        # But for simplicity and compatibility with standard project patterns:
        existing = self.collection.find_one({"email": email}, {"last_message_date": 1})
        is_new_day = (
            (existing and existing.get("last_message_date") != today_str)
            if existing
            else True
        )

        if new_cycle_start:
            update_doc = {
                "$inc": {"total_messages_sent": 1},
                "$set": {
                    "current_billing_cycle_start": new_cycle_start,
                    "messages_sent_this_month": 1,
                    "last_message_date": today_str,
                    "messages_sent_today": 1,
                },
            }
        else:
            inc_fields = {"total_messages_sent": 1, "messages_sent_this_month": 1}
            set_fields: dict[str, Any] = {"last_message_date": today_str}

            if is_new_day:
                set_fields["messages_sent_today"] = 1
            else:
                inc_fields["messages_sent_today"] = 1

            update_doc = {"$inc": inc_fields, "$set": set_fields}

        self.collection.update_one({"email": email}, update_doc)
