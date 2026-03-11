"""
This module contains the repository for logging LLM prompts.
"""

from datetime import datetime, timezone, timedelta
from pymongo.database import Database
from src.repositories.base import BaseRepository


class PromptRepository(BaseRepository):
    """
    Repository for logging LLM prompts to the database.
    """

    def __init__(self, database: Database):
        super().__init__(database, "prompt_logs")

    def log_prompt(self, user_email: str, prompt_data: dict, max_logs: int = 10):
        """
        Logs a prompt for a specific user and ensures only the last `max_logs` are kept.
        """

        # Sanitize data: convert Pydantic models or other non-serializable objects
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sanitize(i) for i in obj]
            if hasattr(obj, "model_dump"):  # Pydantic v2
                return obj.model_dump()
            if hasattr(obj, "dict"):  # Pydantic v1 fallback
                return obj.dict()
            return obj

        sanitized_prompt = sanitize(prompt_data)

        log_entry = {
            "user_email": user_email,
            "timestamp": datetime.now(timezone.utc),
            "prompt": sanitized_prompt,
            "tokens_input": prompt_data.get("tokens_input", 0),
            "tokens_output": prompt_data.get("tokens_output", 0),
            "duration_ms": prompt_data.get("duration_ms", 0),
            "model": prompt_data.get("model", "unknown"),
            "status": prompt_data.get("status", "success"),
        }

        # Insert the new log
        self.collection.insert_one(log_entry)

        # Keep only the last max_logs for this user
        # 1. Find the timestamps of the logs to keep
        logs_to_keep = (
            self.collection.find({"user_email": user_email})
            .sort("timestamp", -1)
            .limit(max_logs)
        )

        keep_ids = [doc["_id"] for doc in logs_to_keep]

        # 2. Delete logs that are NOT in the keep list
        if len(keep_ids) >= max_logs:
            self.collection.delete_many(
                {"user_email": user_email, "_id": {"$nin": keep_ids}}
            )

    def get_user_prompts(self, user_email: str, limit: int = 10):
        """
        Retrieves the last prompts for a specific user.
        """
        return list(
            self.collection.find({"user_email": user_email})
            .sort("timestamp", -1)
            .limit(limit)
        )

    def get_token_summary(self, days: int = 30):
        """
        Retrieves aggregated token consumption per user over the last N days.
        Only includes logs with tokens_input > 0 (real data).
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": start_date},
                    "tokens_input": {"$gt": 0},  # Only real data
                }
            },
            {
                "$group": {
                    "_id": "$user_email",
                    "total_input": {"$sum": "$tokens_input"},
                    "total_output": {"$sum": "$tokens_output"},
                    "message_count": {"$sum": 1},
                    "last_activity": {"$max": "$timestamp"},
                    "model": {"$last": "$model"},
                }
            },
            {"$sort": {"total_input": -1}},
        ]
        return list(self.collection.aggregate(pipeline))

    def get_token_timeseries(self, days: int = 30, user_email: str | None = None):
        """
        Retrieves daily token consumption for charting.
        If user_email is provided, returns data for that user only.
        Otherwise returns aggregated data for all users.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        match_stage = {
            "timestamp": {"$gte": start_date},
            "tokens_input": {"$gt": 0},  # Only real data
        }
        if user_email:
            match_stage["user_email"] = user_email

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp",
                        }
                    },
                    "tokens_input": {"$sum": "$tokens_input"},
                    "tokens_output": {"$sum": "$tokens_output"},
                }
            },
            {"$sort": {"_id": 1}},  # Sort by date ascending
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "tokens_input": 1,
                    "tokens_output": 1,
                }
            },
        ]
        return list(self.collection.aggregate(pipeline))
