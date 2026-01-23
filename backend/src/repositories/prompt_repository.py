from datetime import datetime, timezone
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
        Logs a prompt for a specific user and ensures only the last `max_logs` are kept for that user.
        """
        # Sanitize data: convert Pydantic models or other non-serializable objects
        def sanitize(obj):
            if isinstance(obj, dict):
                return {k: sanitize(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize(i) for i in obj]
            elif hasattr(obj, "model_dump"):  # Pydantic v2
                return obj.model_dump()
            elif hasattr(obj, "dict"):  # Pydantic v1 fallback
                return obj.dict()
            return obj

        sanitized_prompt = sanitize(prompt_data)

        log_entry = {
            "user_email": user_email,
            "timestamp": datetime.now(timezone.utc),
            "prompt": sanitized_prompt
        }
        
        # Insert the new log
        self.collection.insert_one(log_entry)
        
        # Keep only the last max_logs for this user
        # 1. Find the timestamps of the logs to keep
        logs_to_keep = self.collection.find(
            {"user_email": user_email}
        ).sort("timestamp", -1).limit(max_logs)
        
        keep_ids = [doc["_id"] for doc in logs_to_keep]
        
        # 2. Delete logs that are NOT in the keep list
        if len(keep_ids) >= max_logs:
            self.collection.delete_many({
                "user_email": user_email,
                "_id": {"$nin": keep_ids}
            })

    def get_user_prompts(self, user_email: str, limit: int = 10):
        """
        Retrieves the last prompts for a specific user.
        """
        return list(self.collection.find(
            {"user_email": user_email}
        ).sort("timestamp", -1).limit(limit))
