from datetime import datetime, timedelta, timezone
import hashlib
from src.services.database import MongoDatabase


class MetabolismInsightCache:
    def __init__(self, db: MongoDatabase):
        self.db = db
        self.collection = self.db.database["ai_insight_cache"]

    def _generate_key(
        self,
        user_email: str,
        weight_logs: list,
        nutrition_logs: list,
        user_goal: dict,
        trainer_type: str,
    ) -> str:
        """
        Generates a cache key based on RAW data availability.
        Invalidates when:
        - New weight or nutrition log is added (count + last date changes)
        - User goal changes
        - Trainer type changes
        - Hourly (includes current hour in key)
        """
        # Use last date + count as a performant proxy for logs hash
        last_weight = weight_logs[-1].date.isoformat() if weight_logs else "none"
        last_nutrition = (
            nutrition_logs[-1].date.isoformat() if nutrition_logs else "none"
        )

        # Include current hour for hourly invalidation
        # Use UTC to be consistent
        current_hour = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H")

        payload = (
            f"{user_email}:"
            f"h:{current_hour}:"
            f"w:{len(weight_logs)}:{last_weight}:"
            f"n:{len(nutrition_logs)}:{last_nutrition}:"
            f"g:{user_goal.get('goal_type')}:{user_goal.get('weekly_rate')}:"
            f"t:{trainer_type}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self,
        user_email: str,
        weight_logs: list,
        nutrition_logs: list,
        user_goal: dict,
        trainer_type: str,
    ) -> str | None:
        key = self._generate_key(
            user_email, weight_logs, nutrition_logs, user_goal, trainer_type
        )
        doc = self.collection.find_one({"_id": key})

        if doc and doc.get("expires_at").replace(tzinfo=timezone.utc) > datetime.now(
            timezone.utc
        ):
            return doc.get("content")
        return None

    def set(
        self,
        user_email: str,
        weight_logs: list,
        nutrition_logs: list,
        user_goal: dict,
        trainer_type: str,
        content: str,
    ):
        key = self._generate_key(
            user_email, weight_logs, nutrition_logs, user_goal, trainer_type
        )
        now = datetime.now(timezone.utc)
        self.collection.update_one(
            {"_id": key},
            {
                "$set": {
                    "content": content,
                    "created_at": now,
                    # Expire in 1 hour (redundant with key but good for DB cleanup)
                    "expires_at": now + timedelta(hours=1),
                    "user_email": user_email,
                }
            },
            upsert=True,
        )
