from datetime import datetime, timedelta
import hashlib
import json
from src.services.database import MongoDatabase

class MetabolismInsightCache:
    def __init__(self, db: MongoDatabase):
        self.db = db
        self.collection = self.db.database["ai_insight_cache"]

    def _generate_key(self, user_email: str, stats: dict, trainer_summary: str) -> str:
        """
        Generates a stable cache key based on input data.
        Any change in stats (TDEE, weight, log counts) or trainer profile invalidates the key.
        """
        # Create a stable, sorted dictionary string for stats
        # Round floats to avoid micro-precision flip-flops
        stable_stats = {
            k: (round(v, 2) if isinstance(v, float) else v) 
            for k, v in stats.items()
            if k not in ["message", "startDate", "endDate"] # Exclude informational fields that don't affect logic
        }
        
        # We also depend on the DATE, so the insight is refreshed daily even if data is same
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        payload = f"{user_email}:{today_str}:{json.dumps(stable_stats, sort_keys=True)}:{trainer_summary}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, user_email: str, stats: dict, trainer_summary: str) -> str | None:
        key = self._generate_key(user_email, stats, trainer_summary)
        doc = self.collection.find_one({"_id": key})
        
        if doc and doc.get("expires_at") > datetime.utcnow():
            return doc.get("content")
        return None

    def set(self, user_email: str, stats: dict, trainer_summary: str, content: str):
        key = self._generate_key(user_email, stats, trainer_summary)
        self.collection.update_one(
            {"_id": key},
            {
                "$set": {
                    "content": content,
                    "created_at": datetime.utcnow(),
                    "expires_at": datetime.utcnow() + timedelta(hours=24),
                    "user_email": user_email
                }
            },
            upsert=True
        )
