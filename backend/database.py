import bcrypt
import pymongo

from .config import settings
from .models import TrainerProfile, UserProfile, ChatHistory
from langchain_mongodb import MongoDBChatMessageHistory
from .logs import logger

from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime

client = pymongo.MongoClient(settings.MONGO_URI)
database = client[settings.DB_NAME]


class MongoDatabase:
    def save_user_profile(self, profile: UserProfile):
        """
        Saves or updates a user profile in the database.

        If a user with the given email already exists, their profile is updated with the new data.
        If no user with the given email exists, a new user profile is inserted.

        Args:
            profile (UserProfile): The user profile data to save or update.

        Returns:
            None
        """
        db = self._get_db()
        db.users.update_one(
            {"email": profile.email}, {"$set": profile.model_dump()}, upsert=True
        )

    def _get_db(self):
        """Returns the configured MongoDB connection."""
        return database

    def get_user_profile(self, email: str) -> UserProfile | None:
        """
        Retrieve a user profile from the database by email.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            UserProfile | None: The user profile object if found, otherwise None.
        """
        db = self._get_db()
        user_data = db.users.find_one({"email": email})
        if not user_data:
            return None
        return UserProfile(**user_data)

    def validate_user(self, email: str, password: str) -> bool:
        """
        Validates user credentials by checking if the provided email exists in the database and if the given password matches the stored password hash.

        Args:
            email (str): The user's email address.
            password (str): The user's plaintext password.

        Returns:
            bool: True if the credentials are valid, False otherwise.
        """
        db = self._get_db()
        user = db.users.find_one({"email": email})
        if not user:
            return False
        password_hash = user.get("password_hash", "")
        if bcrypt.checkpw(password.encode(), password_hash.encode()):
            return True
        return False

    def save_trainer_profile(self, trainer_profile: TrainerProfile) -> None:
        """
        Saves the provided trainer profile to the database.

        Args:
            trainer_profile (TrainerProfile): The trainer profile to be saved.
        """
        db = self._get_db()
        db.trainer_profiles.update_one(
            {"user_email": trainer_profile.user_email},
            {"$set": trainer_profile.model_dump()},
            upsert=True,
        )

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """
        Retrieves the trainer profile associated with the given email address from the database.

        Args:
            email (str): The user's email address.

        Returns:
            TrainerProfile or None: The trainer profile if found, otherwise None.
        """
        db = self._get_db()
        trainer_profile = db.trainer_profiles.find_one({"user_email": email})
        if not trainer_profile:
            return None
        return TrainerProfile(**trainer_profile)

    def get_chat_history(self, user_id: str) -> list[ChatHistory]:
        """Retrieves the chat history for a given user.

        Args:
            user_id (str): The unique identifier of the user whose chat history is being retrieved.

        Returns:
            list[ChatHistory]: A list of ChatHistory objects representing the chat history ordered by timestamp.
        """
        logger.debug("Retrieving chat history for session: %s", user_id)
        history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=user_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )
        return ChatHistory.from_mongodb_chat_message_history(history)

    def add_to_history(
        self,
        chat_history: ChatHistory,
        session_id: str,
    ):
        """Adds user and AI messages to the chat history, with timestamp."""
        logger.debug("Adding messages to chat history with timestamp.")
        now = datetime.now().isoformat()
        chat_history_mongo = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )
        if chat_history.sender == "Trainer":
            chat_history_mongo.add_message(
                AIMessage(
                    content=chat_history.text, additional_kwargs={"timestamp": now}
                )
            )
        else:
            HumanMessage(
                content=chat_history.text, additional_kwargs={"timestamp": now}
            )
