import bcrypt
import pymongo

from .config import settings
from .models import ConversationSummary, TrainerProfile, UserProfile

client = pymongo.MongoClient(settings.MONGO_URI)
database = client[settings.DB_NAME]


def save_user_profile(profile: UserProfile):
    """
    Saves or updates a user profile in the database.

    If a user with the given email already exists, their profile is updated with the new data.
    If no user with the given email exists, a new user profile is inserted.

    Args:
        profile (UserProfile): The user profile data to save or update.

    Returns:
        None
    """
    db = _get_db()
    db.users.update_one(
        {"email": profile.email}, {"$set": profile.model_dump()}, upsert=True
    )


def _get_db():
    """Returns the configured MongoDB connection."""
    return database


def get_user_profile(email: str) -> UserProfile | None:
    """
    Retrieve a user profile from the database by email.

    Args:
        email (str): The email address of the user to retrieve.

    Returns:
        UserProfile | None: The user profile object if found, otherwise None.
    """
    db = _get_db()
    user_data = db.users.find_one({"email": email})
    if not user_data:
        return None
    return UserProfile(**user_data)


def validate_user(email: str, password: str) -> bool:
    """
    Validates user credentials by checking if the provided email exists in the database and if the given password matches the stored password hash.

    Args:
        email (str): The user's email address.
        password (str): The user's plaintext password.

    Returns:
        bool: True if the credentials are valid, False otherwise.
    """
    db = _get_db()
    user = db.users.find_one({"email": email})
    if not user:
        return False
    password_hash = user.get("password_hash", "")
    if bcrypt.checkpw(password.encode(), password_hash.encode()):
        return True
    return False


def save_trainer_profile(trainer_profile: TrainerProfile) -> None:
    """
    Saves the provided trainer profile to the database.

    Args:
        trainer_profile (TrainerProfile): The trainer profile to be saved.
    """
    db = _get_db()
    db.trainer_profiles.update_one(
        {"user_email": trainer_profile.user_email},
        {"$set": trainer_profile.model_dump()},
        upsert=True
    )


def get_trainer_profile(email: str) -> TrainerProfile | None:
    """
    Retrieves the trainer profile associated with the given email address from the database.

    Args:
        email (str): The user's email address.

    Returns:
        TrainerProfile or None: The trainer profile if found, otherwise None.
    """
    db = _get_db()
    trainer_profile = db.trainer_profiles.find_one({"user_email": email})
    if not trainer_profile:
        return None
    return TrainerProfile(**trainer_profile)


def save_conversation_summary(summary: ConversationSummary) -> None:
    """
    Saves or updates a conversation summary in the database.

    If a summary with the given user_email already exists, it is updated with the new data.
    If no summary with the given user_email exists, a new summary is inserted.

    Args:
        summary (ConversationSummary): The conversation summary data to save or update.

    Returns:
        None
    """
    db = _get_db()
    db.conversation_summaries.update_one(
        {"user_email": summary.user_email},
        {"$set": summary.model_dump()},
        upsert=True
    )


def get_conversation_summary(email: str) -> ConversationSummary | None:
    """
    Retrieves the conversation summary associated with the given email address from the database.

    Args:
        email (str): The user's email address.

    Returns:
        ConversationSummary or None: The conversation summary if found, otherwise None.
    """
    db = _get_db()
    summary_data = db.conversation_summaries.find_one({"user_email": email})
    if not summary_data:
        return None
    return ConversationSummary(**summary_data)
