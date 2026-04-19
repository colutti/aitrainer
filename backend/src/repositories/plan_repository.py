"""Repository for central plan versions and active-plan lifecycle."""

from datetime import datetime

import pymongo
from pymongo.database import Database

from src.api.models.plan import ActivePlan, PlanStatus
from src.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    """MongoDB repository for user plan versions."""

    def __init__(self, database: Database):
        super().__init__(database, "plans")
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Ensure indexes required for plan version operations."""
        self.collection.create_index("user_email")
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING), ("version", pymongo.ASCENDING)],
            unique=True,
        )
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING), ("status", pymongo.ASCENDING)]
        )

    def save_plan(self, plan: ActivePlan) -> str:
        """Upserts a plan version and returns its document id."""
        payload = plan.model_dump(exclude={"id"})
        payload["updated_at"] = datetime.now()

        query = {"user_email": plan.user_email, "version": plan.version}
        result = self.collection.update_one(query, {"$set": payload}, upsert=True)
        if result.upserted_id is not None:
            return str(result.upserted_id)

        existing = self.collection.find_one(query, {"_id": 1})
        return str(existing["_id"]) if existing else ""

    def get_active_plan(self, user_email: str) -> ActivePlan | None:
        """Returns currently active plan for user."""
        doc = self.collection.find_one(
            {"user_email": user_email, "status": PlanStatus.ACTIVE.value}
        )
        return ActivePlan(**doc) if doc else None

    def get_latest_plan(self, user_email: str) -> ActivePlan | None:
        """Returns latest version regardless of status."""
        doc = self.collection.find_one(
            {"user_email": user_email},
            sort=[("version", pymongo.DESCENDING)],
        )
        return ActivePlan(**doc) if doc else None

    def list_plan_versions(self, user_email: str) -> list[ActivePlan]:
        """Returns all versions from latest to oldest."""
        cursor = self.collection.find({"user_email": user_email}).sort(
            "version", pymongo.DESCENDING
        )
        return [ActivePlan(**doc) for doc in cursor]

    def approve_plan(self, user_email: str, version: int) -> bool:
        """Transition awaiting_approval version to active and archive current active."""
        now = datetime.now()
        self.collection.update_many(
            {"user_email": user_email, "status": PlanStatus.ACTIVE.value},
            {"$set": {"status": PlanStatus.ARCHIVED.value, "updated_at": now}},
        )

        result = self.collection.update_one(
            {
                "user_email": user_email,
                "version": version,
                "status": PlanStatus.AWAITING_APPROVAL.value,
            },
            {"$set": {"status": PlanStatus.ACTIVE.value, "updated_at": now}},
        )
        return result.matched_count > 0

    def archive_active_plan(self, user_email: str) -> bool:
        """Archives active plan for user."""
        result = self.collection.update_one(
            {"user_email": user_email, "status": PlanStatus.ACTIVE.value},
            {
                "$set": {
                    "status": PlanStatus.ARCHIVED.value,
                    "updated_at": datetime.now(),
                }
            },
        )
        return result.modified_count > 0
