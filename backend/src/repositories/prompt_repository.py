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
        
        Args:
            user_email: The email of the user who triggered the prompt.
            prompt_data: The full prompt data (messages, input, etc.).
            max_logs: Maximum number of logs to keep per user.
        """
        log_entry = {
            "user_email": user_email,
            "timestamp": datetime.now(timezone.utc),
            "prompt": prompt_data
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
