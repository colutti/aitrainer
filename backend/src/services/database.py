"""
This module contains the database logic for the application.
"""
from datetime import datetime
import bcrypt
import pymongo
from langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel
from langchain_classic.memory import ConversationSummaryBufferMemory

from src.core.config import settings
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.user_profile import UserProfile
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.workout_log import WorkoutLog, WorkoutWithId
from src.core.logs import logger
from src.api.models.workout_stats import WorkoutStats, PersonalRecord, VolumeStat
from datetime import timedelta
import calendar





class MongoDatabase:
    """
    This class handles all the database operations.
    """
    def __init__(self):
        try:
            self.client = pymongo.MongoClient(settings.MONGO_URI)
            self.database = self.client[settings.DB_NAME]
            logger.info("Successfully connected to MongoDB.")
        except pymongo.errors.ConnectionFailure as e: # type: ignore
            logger.error("Failed to connect to MongoDB: %s", e)
            raise

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
        result = self.database.users.update_one(
            {"email": profile.email}, {"$set": profile.model_dump()}, upsert=True
        )
        if result.upserted_id:
            logger.info("New user profile created for email: %s", profile.email)
        elif result.modified_count > 0:
            logger.info("User profile updated for email: %s", profile.email)
        else:
            logger.debug("User profile for email %s already up-to-date or no changes.", profile.email)


    def get_user_profile(self, email: str) -> UserProfile | None:
        """
        Retrieve a user profile from the database by email.

        Args:
            email (str): The email address of the user to retrieve.

        Returns:
            UserProfile | None: The user profile object if found, otherwise None.
        """
        user_data = self.database.users.find_one({"email": email})
        if not user_data:
            logger.info("User profile not found for email: %s", email)
            return None
        logger.debug("User profile retrieved for email: %s", email)
        return UserProfile(**user_data)


    def validate_user(self, email: str, password: str) -> bool:
        """
        Validates user credentials by checking if the provided email
        exists in the database and if the given password matches the stored
        password hash.

        Args:
            email (str): The user's email address.
            password (str): The user's plaintext password.

        Returns:
            bool: True if the credentials are valid, False otherwise.
        """
        user = self.database.users.find_one({"email": email})
        if not user:
            logger.debug("Login attempt for non-existent user: %s", email)
            return False
        password_hash = user.get("password_hash", "")
        if bcrypt.checkpw(password.encode(), password_hash.encode()):
            logger.debug("Successful password validation for user: %s", email)
            return True
        logger.debug("Failed password validation for user: %s", email)
        return False

    def save_trainer_profile(self, trainer_profile: TrainerProfile) -> None:
        """
        Saves the provided trainer profile to the database.

        Args:
            trainer_profile (TrainerProfile): The trainer profile to be saved.
        """
        result = self.database.trainer_profiles.update_one(
            {"user_email": trainer_profile.user_email},
            {"$set": trainer_profile.model_dump()},
            upsert=True,
        )
        if result.upserted_id:
            logger.info("New trainer profile created for user: %s", trainer_profile.user_email)
        elif result.modified_count > 0:
            logger.info("Trainer profile updated for user: %s", trainer_profile.user_email)
        else:
            logger.debug("Trainer profile for user %s already up-to-date or no changes.", trainer_profile.user_email)


    def get_trainer_profile(self, email: str) -> TrainerProfile | None:
        """
        Retrieves the trainer profile associated with the given email address from the database.

        Args:
            email (str): The user's email address.

        Returns:
            TrainerProfile or None: The trainer profile if found, otherwise None.
        """
        trainer_profile = self.database.trainer_profiles.find_one({"user_email": email})
        if not trainer_profile:
            logger.info("Trainer profile not found for email: %s", email)
            return None
        logger.debug("Trainer profile retrieved for email: %s", email)
        return TrainerProfile(**trainer_profile)

    def get_chat_history(self, user_id: str, limit: int = 20) -> list[ChatHistory]:
        """Retrieves the chat history for a given user.

        Args:
            user_id (str): The unique identifier of the user whose
                chat history is being retrieved.
            limit (int): Maximum number of messages to retrieve (default: 20).

        Returns:
            list[ChatHistory]: A list of ChatHistory objects representing
                the chat history ordered by timestamp, limited to the most recent messages.
        """
        logger.debug("Retrieving chat history for session: %s (limit: %d)", user_id, limit)
        history = MongoDBChatMessageHistory(
            connection_string=settings.MONGO_URI,
            session_id=user_id,
            database_name=settings.DB_NAME,
            history_size=limit,  # Use the limit parameter
        )
        return ChatHistory.from_mongodb_chat_message_history(history)

    def add_to_history(
        self,
        chat_history: ChatHistory,
        session_id: str,
        trainer_type: str | None = None,
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
        
        additional_kwargs = {"timestamp": now}
        if trainer_type:
            additional_kwargs["trainer_type"] = trainer_type

        if chat_history.sender == Sender.TRAINER:
            chat_history_mongo.add_message(
                AIMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )
        else:
            chat_history_mongo.add_message(
                HumanMessage(
                    content=chat_history.text, additional_kwargs=additional_kwargs
                )
            )

    def _get_chat_message_history(self, session_id: str) -> MongoDBChatMessageHistory:
        """
        Returns the raw MongoDBChatMessageHistory for a session.
        
        Args:
            session_id: User email (session identifier)
            
        Returns:
            MongoDBChatMessageHistory instance
        """
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
        """
        Returns a ConversationSummaryBufferMemory backed by MongoDB.
        
        This memory automatically summarizes older messages when the buffer
        exceeds max_token_limit, providing "infinite memory" with bounded tokens.
        
        Args:
            session_id: User email (session identifier)
            llm: LLM instance for generating summaries
            max_token_limit: When to trigger summarization (default: from settings)
        
        Returns:
            Memory object that auto-summarizes when buffer exceeds limit
        """
        if max_token_limit is None:
            max_token_limit = settings.SUMMARY_MAX_TOKEN_LIMIT
            
        chat_history = self._get_chat_message_history(session_id)
        
        return ConversationSummaryBufferMemory(
            llm=llm,
            chat_memory=chat_history,
            max_token_limit=max_token_limit,
            return_messages=True,
            memory_key="chat_history",
            human_prefix="Aluno",
            ai_prefix="Treinador",
        )

    def add_token_to_blocklist(self, token: str, expires_at: datetime) -> None:
        """
        Adds a JWT token to the blocklist collection.

        Args:
            token (str): The JWT token to blocklist.
            expires_at (datetime): When the token expires (for TTL cleanup).
        """
        self.database.token_blocklist.update_one(
            {"token": token},
            {"$set": {"token": token, "expires_at": expires_at}},
            upsert=True,
        )
        logger.debug("Token added to blocklist.")

    def is_token_blocklisted(self, token: str) -> bool:
        """
        Checks if a token is in the blocklist.

        Args:
            token (str): The JWT token to check.

        Returns:
            bool: True if the token is blocklisted, False otherwise.
        """
        result = self.database.token_blocklist.find_one({"token": token})
        return result is not None

    def ensure_blocklist_indexes(self) -> None:
        """
        Ensures the blocklist collection has proper indexes.
        Creates a TTL index on expires_at to automatically remove expired tokens.
        """
        self.database.token_blocklist.create_index(
            "expires_at", expireAfterSeconds=0
        )
        logger.info("Blocklist TTL index ensured.")

    def save_workout_log(self, workout: WorkoutLog) -> str:
        """
        Saves a workout log to the database.

        Args:
            workout (WorkoutLog): The workout log to save.

        Returns:
            str: The inserted document ID as a string.
        """
        result = self.database.workout_logs.insert_one(workout.model_dump())
        logger.info(
            "Workout log saved for user %s with %d exercises",
            workout.user_email,
            len(workout.exercises),
        )
        return str(result.inserted_id)

    def get_workout_logs(
        self, user_email: str, limit: int = 50
    ) -> list[WorkoutLog]:
        """
        Retrieves workout logs for a given user.

        Args:
            user_email (str): The user's email address.
            limit (int): Maximum number of workout logs to retrieve (default: 50).

        Returns:
            list[WorkoutLog]: A list of workout logs ordered by date descending.
        """
        cursor = (
            self.database.workout_logs.find({"user_email": user_email})
            .sort("date", pymongo.DESCENDING)
            .limit(limit)
        )
        workouts = [WorkoutLog(**doc) for doc in cursor]
        logger.debug(
            "Retrieved %d workout logs for user: %s", len(workouts), user_email
        )
        return workouts

    def get_workouts_paginated(
        self, user_email: str, page: int = 1, page_size: int = 10, workout_type: str | None = None
    ) -> tuple[list[dict], int]:
        """
        Retrieves workout logs for a given user with pagination and optional filtering.

        Args:
            user_email (str): The user's email address.
            page (int): Page number (1-indexed).
            page_size (int): Number of items per page.
            workout_type (str | None): Filter by workout type.

        Returns:
            tuple[list[dict], int]: List of workout dicts (with 'id') and total count.
        """
        query = {"user_email": user_email}
        if workout_type:
            query["workout_type"] = workout_type

        total = self.database.workout_logs.count_documents(query)
        
        skip = (page - 1) * page_size
        cursor = (
            self.database.workout_logs.find(query)
            .sort("date", pymongo.DESCENDING)
            .skip(skip)
            .limit(page_size)
        )
        
        workouts = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            workouts.append(doc)
        
        logger.debug(
            "Retrieved %d/%d workout logs for user: %s (page %d)",
            len(workouts), total, user_email, page
        )
        return workouts, total

    def get_workout_stats(self, user_email: str) -> WorkoutStats:
        """
        Calculates and returns workout statistics for the dashboard.
        """
        # 1. Get all workouts (projection for speed)
        cursor = self.database.workout_logs.find(
            {"user_email": user_email},
            {"date": 1, "workout_type": 1, "exercises": 1, "user_email": 1, "duration_minutes": 1}
        ).sort("date", pymongo.DESCENDING)
        
        all_workouts = list(cursor)
        if not all_workouts:
            return WorkoutStats(
                current_streak_weeks=0,
                weekly_frequency=[False]*7,
                weekly_volume=[],
                recent_prs=[],
                total_workouts=0,
                last_workout=None
            )

        # 2. Total Workouts
        total_workouts = len(all_workouts)

        # 3. Last Workout
        last_workout_doc = all_workouts[0]
        last_workout_doc["id"] = str(last_workout_doc.pop("_id"))
        last_workout = WorkoutWithId(**last_workout_doc)

        # 4. Streak (Weeks with >= 3 workouts)
        current_streak = self._calculate_weekly_streak(all_workouts)

        # 5. Weekly Metrics (Frequency & Volume)
        freq, volume = self._calculate_weekly_metrics(all_workouts)

        # 6. Recent PRs
        prs = self._calculate_recent_prs(all_workouts)

        return WorkoutStats(
            current_streak_weeks=current_streak,
            weekly_frequency=freq,
            weekly_volume=volume,
            recent_prs=prs,
            total_workouts=total_workouts,
            last_workout=last_workout
        )

    def _calculate_weekly_streak(self, workouts: list[dict]) -> int:
        """
        Calculates consecutive weeks with >= 3 workouts.
        """
        if not workouts:
            return 0
            
        # Group workouts by (iso_year, iso_week)
        weeks_data = {}
        for w in workouts:
            dt = w["date"]
            iso_year, iso_week, _ = dt.isocalendar()
            key = (iso_year, iso_week)
            weeks_data[key] = weeks_data.get(key, 0) + 1

        # Check existing streak counting backwards from current week
        now = datetime.now()
        current_year, current_week, _ = now.isocalendar()
        
        streak = 0
        # If current week has met criteria, start counting from it
        # If not, check if previous week met criteria (streak active but not yet updated this week)
        
        # Helper to check criterion
        def met_criteria(y, w):
            return weeks_data.get((y, w), 0) >= 3

        # Start checking from current week
        check_year, check_week = current_year, current_week
        
        # If current week didn't meet criteria yet, allow it to "continue" if previous week did?
        # Standard streak: count completed blocks.
        # If I have 3 workouts this week -> streak + 1.
        # If I have 1 workout this week -> streak continues? "Weekly Streak" usually implies completed weeks.
        # But for "Current Streak", valid weeks immediately preceding now.
        
        while met_criteria(check_year, check_week):
            streak += 1
            # Move to previous week
            check_date = datetime.fromisocalendar(check_year, check_week, 1) - timedelta(days=7)
            check_year, check_week, _ = check_date.isocalendar()
            
        return streak

    def _calculate_weekly_metrics(self, workouts: list[dict]) -> tuple[list[bool], list[VolumeStat]]:
        """
        Calculates weekly frequency (Bool list) and volume per category.
        """
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday()) # Mon
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        current_week_workouts = [w for w in workouts if w["date"] >= start_of_week]
        
        # Frequency (Mon-Sun)
        freq = [False] * 7
        for w in current_week_workouts:
            day_idx = w["date"].weekday() # 0=Mon, 6=Sun
            freq[day_idx] = True
            
        # Volume
        volume_map = {}
        for w in current_week_workouts:
            cat = w.get("workout_type", "Outros") or "Outros"
            exercises = w.get("exercises", [])
            for ex in exercises:
                # Calculate volume for this exercise
                # ex is dict here because we fetched raw dicts
                reps_list = ex.get("reps_per_set", [])
                weights_list = ex.get("weights_per_set", [])
                
                vol = 0.0
                for i, reps in enumerate(reps_list):
                    weight = weights_list[i] if i < len(weights_list) else 0.0
                    vol += reps * weight
                
                volume_map[cat] = volume_map.get(cat, 0.0) + vol
                
        # Convert to list
        volume_stats = [
            VolumeStat(category=k, volume=round(v, 1)) 
            for k, v in volume_map.items()
        ]
        
        # Sort by volume desc
        volume_stats.sort(key=lambda x: x.volume, reverse=True)
        return freq, volume_stats

    def _calculate_recent_prs(self, workouts: list[dict], limit: int = 3) -> list[PersonalRecord]:
        """
        Identifies the top 3 most recent Personal Records (max weight).
        """
        # Map: Exercise Name -> (Max Weight, Date, Reps, WorkoutID)
        max_weights = {} 
        
        # Traverse from oldest to newest to build history?
        # No, we want "Recent PRs". This implies the PR *date* is recent.
        # A PR is the ALL-TIME max.
        # So we iterate ALL workouts to find the ALL-TIME max for each exercise.
        # Then we look at WHEN that max was achieved.
        
        # Iterate all workouts (reversed: Oldest -> Newest) to find first/last occurrence?
        # We need the DATE of the PR. If I tie my PR, does the date update? 
        # Usually "New PR" implies exceeding previous.
        
        for w in reversed(workouts): # Oldest to Newest
            w_id = str(w.get("_id"))
            date = w["date"]
            exercises = w.get("exercises", [])
            
            for ex in exercises:
                name = ex.get("name")
                if not name: continue
                
                weights = ex.get("weights_per_set", [])
                reps = ex.get("reps_per_set", [])
                
                if not weights: continue
                
                # Find max in this session
                session_max = -1.0
                session_max_reps = 0
                
                for i, weight in enumerate(weights):
                    if weight > session_max:
                        session_max = weight
                        session_max_reps = reps[i] if i < len(reps) else 0
                
                if session_max > 0:
                    current_record = max_weights.get(name)
                    # If beats record, update
                    if not current_record or session_max > current_record["weight"]:
                        max_weights[name] = {
                            "weight": session_max,
                            "reps": session_max_reps,
                            "date": date,
                            "workout_id": w_id
                        }
        
        # Convert map to list and sort by date desc
        prs_list = [
            PersonalRecord(
                exercise_name=name,
                weight=data["weight"],
                reps=data["reps"],
                date=data["date"],
                workout_id=data["workout_id"]
            )
            for name, data in max_weights.items()
        ]
        
        prs_list.sort(key=lambda x: x.date, reverse=True)
        return prs_list[:limit]

    def get_workout_types(self, user_email: str) -> list[str]:
        """
        Retrieves all distinct workout types for a user.
        """
        types = self.database.workout_logs.distinct("workout_type", {"user_email": user_email})
        return sorted([t for t in types if t])
