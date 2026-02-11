"""
This module contains the database logic for the application.
"""

from datetime import datetime, date
import pymongo
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.language_models import BaseChatModel
from langchain_classic.memory import ConversationSummaryBufferMemory

from src.core.config import settings
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.api.models.chat_history import ChatHistory
from src.api.models.weight_log import WeightLog
from src.api.models.workout_log import WorkoutLog, WorkoutWithId
from src.core.logs import logger
from src.api.models.workout_stats import WorkoutStats
from src.api.models.nutrition_log import NutritionLog
from src.api.models.nutrition_stats import NutritionStats

from src.repositories.user_repository import UserRepository
from src.repositories.trainer_repository import TrainerRepository
from src.repositories.token_repository import TokenRepository
from src.repositories.chat_repository import ChatRepository
from src.repositories.workout_repository import WorkoutRepository
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.weight_repository import WeightRepository
from src.repositories.invite_repository import InviteRepository
from src.repositories.prompt_repository import PromptRepository
from src.repositories.telegram_repository import TelegramRepository
from src.services.adaptive_tdee import AdaptiveTDEEService


# pylint: disable=too-many-instance-attributes
class MongoDatabase:
    """
    This class handles all the database operations.
    """
    # pylint: disable=too-many-public-methods

    def __init__(self):
        try:
            self.client = pymongo.MongoClient(settings.MONGO_URI)
            self.database = self.client[settings.DB_NAME]

            # Initialize Repositories
            self.users = UserRepository(self.database)
            self.trainers = TrainerRepository(self.database)
            self.tokens = TokenRepository(self.database)
            self.chat = ChatRepository(self.database)
            self.workouts_repo = WorkoutRepository(self.database)
            self.nutrition = NutritionRepository(self.database)
            self.weight = WeightRepository(self.database)
            self.invites = InviteRepository(self.database)
            self.prompts = PromptRepository(self.database)
            self.telegram = TelegramRepository(self.database)

            logger.info("Successfully connected to MongoDB.")
        except pymongo.errors.ConnectionFailure as e:  # type: ignore
            logger.error("Failed to connect to MongoDB: %s", e)
            raise

    def close(self):
        """
        Closes the MongoDB connection.
        """
        if hasattr(self, "client"):
            self.client.close()
            logger.info("MongoDB connection closed.")

    def __del__(self):
        """
        Destructor to ensure client is closed.
        """
        self.close()

    def save_user_profile(self, profile: UserProfile):
        """Saves user profile."""
        return self.users.save_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict):
        """Updates specific fields in user profile."""
        return self.users.update_profile_fields(email, fields)

    def get_user_profile(self, email: str) -> UserProfile | None:
        """Retrieves user profile."""
        return self.users.get_profile(email)

    def validate_user(self, email: str, password: str) -> bool:
        """Validates user credentials."""
        return self.users.validate_credentials(email, password)

    def save_trainer_profile(self, trainer_profile: TrainerProfile) -> None:
        """Saves trainer profile."""
        return self.trainers.save_profile(trainer_profile)

    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """Retrieves trainer profile."""
        return self.trainers.get_profile(email)

    def add_token_to_blocklist(self, token: str, expires_at: datetime) -> None:
        """Adds JWT token to blocklist."""
        return self.tokens.add_to_blocklist(token, expires_at)

    def is_token_blocklisted(self, token: str) -> bool:
        """Checks if token is blocklisted."""
        return self.tokens.is_blocklisted(token)

    def ensure_blocklist_indexes(self) -> None:
        """Ensures TTL indexes for token blocklist."""
        return self.tokens.ensure_indexes()

    def get_chat_history(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> list[ChatHistory]:
        """Retrieves chat history."""
        return self.chat.get_history(user_id, limit, offset)

    def add_to_history(
        self,
        chat_history: ChatHistory,
        session_id: str,
        trainer_type: str | None = None,
    ):
        """Adds a message to chat history."""
        return self.chat.add_message(chat_history, session_id, trainer_type)

    def log_prompt(self, user_email: str, prompt_data: dict):
        """
        Logs an LLM prompt for debugging purposes.
        """
        return self.prompts.log_prompt(
            user_email, prompt_data, settings.MAX_PROMPT_LOGS
        )

    def _get_chat_message_history(self, session_id: str) -> MongoDBChatMessageHistory:
        # Deprecated: functionality moved to repository
        return MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=session_id,
            database_name=settings.DB_NAME,
            history_size=settings.MAX_SHORT_TERM_MEMORY_MESSAGES,
        )

    def get_conversation_memory(
        self,
        session_id: str,
        llm: BaseChatModel,
        max_token_limit: int | None = None,
    ) -> ConversationSummaryBufferMemory:
        """Retrieves conversation memory buffer."""
        return self.chat.get_memory_buffer(session_id, llm, max_token_limit)

    def get_window_memory(
        self,
        session_id: str,
        k: int = 40,
    ):
        """
        Returns a ConversationBufferWindowMemory (k messages).
        """
        return self.chat.get_window_memory(session_id, k)

    # ====== WORKOUT REPOSITORY DELEGATION ======
    def save_workout_log(self, workout: WorkoutLog) -> str:
        """Delegates to workout repository."""
        return self.workouts_repo.save_log(workout)

    def get_workout_logs(self, user_email: str, limit: int = 50) -> list[WorkoutWithId]:
        """Delegates to workout repository."""
        return self.workouts_repo.get_logs(user_email, limit)

    def get_workouts_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
        workout_type: str | None = None,
    ) -> tuple[list[dict], int]:
        """Delegates to workout repository."""
        return self.workouts_repo.get_paginated(
            user_email, page, page_size, workout_type
        )

    def get_workout_stats(self, user_email: str) -> WorkoutStats:
        """Delegates to workout repository."""
        return self.workouts_repo.get_stats(user_email)

    def get_workout_types(self, user_email: str) -> list[str]:
        """Delegates to workout repository."""
        return self.workouts_repo.get_types(user_email)

    def delete_workout_log(self, workout_id: str) -> bool:
        """Delegates to workout repository."""
        return self.workouts_repo.delete_log(workout_id)

    def get_workout_by_id(self, workout_id: str) -> dict | None:
        """Delegates to workout repository."""
        return self.workouts_repo.get_log_by_id(workout_id)

    # ====== NUTRITION REPOSITORY DELEGATION ======
    def ensure_nutrition_indexes(self) -> None:
        """Delegates to nutrition repository."""
        return self.nutrition.ensure_indexes()

    def save_nutrition_log(self, log: NutritionLog) -> tuple[str, bool]:
        """Delegates to nutrition repository."""
        return self.nutrition.save_log(log)

    def get_nutrition_logs(
        self, user_email: str, limit: int = 30
    ) -> list[NutritionLog]:
        """Delegates to nutrition repository."""
        return self.nutrition.get_logs(user_email, limit)

    def get_nutrition_logs_by_date_range(
        self, user_email: str, start_date: datetime, end_date: datetime
    ) -> list[NutritionLog]:
        """Delegates to nutrition repository."""
        return self.nutrition.get_logs_by_date_range(user_email, start_date, end_date)

    def get_nutrition_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
        days: int | None = None,
    ) -> tuple[list[dict], int]:
        """Delegates to nutrition repository."""
        return self.nutrition.get_paginated(user_email, page, page_size, days)

    def get_nutrition_stats(self, user_email: str) -> NutritionStats:
        """Delegates to nutrition repository."""
        try:
            tdee_service = AdaptiveTDEEService(self)
        except Exception:  # pylint: disable=broad-exception-caught
            tdee_service = None
        return self.nutrition.get_stats(user_email, tdee_service)

    def delete_nutrition_log(self, log_id: str) -> bool:
        """Delegates to nutrition repository."""
        return self.nutrition.delete_log(log_id)

    def get_nutrition_by_id(self, log_id: str) -> dict | None:
        """Delegates to nutrition repository."""
        return self.nutrition.get_log_by_id(log_id)

    # ====== WEIGHT REPOSITORY DELEGATION ======
    def ensure_weight_indexes(self) -> None:
        """Delegates to weight repository."""
        return self.weight.ensure_indexes()

    def save_weight_log(self, log: WeightLog) -> tuple[str, bool]:
        """Delegates to weight repository."""
        return self.weight.save_log(log)

    def delete_weight_log(self, user_email: str, log_date: date) -> bool:
        """Delegates to weight repository."""
        return self.weight.delete_log(user_email, log_date)

    def get_weight_logs(self, user_email: str, limit: int = 30) -> list[WeightLog]:
        """Delegates to weight repository."""
        return self.weight.get_logs(user_email, limit)

    def get_weight_logs_by_date_range(
        self, user_email: str, start_date: date, end_date: date
    ) -> list[WeightLog]:
        """Delegates to weight repository."""
        return self.weight.get_logs_by_date_range(user_email, start_date, end_date)

    def get_weight_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """Delegates to weight repository."""
        return self.weight.get_paginated(user_email, page, page_size)
