"""Repository for central plan versions and active-plan lifecycle."""

from datetime import datetime

import pymongo
from pymongo import ReturnDocument
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
        """Upserts singleton plan per user and returns its document id."""
        payload = plan.model_dump(exclude={"id"})
        payload["updated_at"] = datetime.now()
        payload["status"] = PlanStatus.ACTIVE.value
        payload["version"] = 1

        doc = self.collection.find_one_and_update(
            {"user_email": plan.user_email},
            {"$set": payload},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            return ""
        self.collection.delete_many(
            {"user_email": plan.user_email, "_id": {"$ne": doc["_id"]}}
        )
        return str(doc["_id"])

    def get_active_plan(self, user_email: str) -> ActivePlan | None:
        """Returns singleton plan for user."""
        doc = self.collection.find_one(
            {"user_email": user_email},
            sort=[("updated_at", pymongo.DESCENDING)],
        )
        return ActivePlan(**doc) if doc else None

    def get_latest_plan(self, user_email: str) -> ActivePlan | None:
        """Returns singleton plan (same as active)."""
        return self.get_active_plan(user_email)

    def list_plan_versions(self, user_email: str) -> list[ActivePlan]:
        """Returns singleton plan list for compatibility."""
        plan = self.get_active_plan(user_email)
        return [plan] if plan else []

    def approve_plan(self, user_email: str, version: int) -> bool:
        """Deprecated in singleton flow: approval is not required."""
        _ = (user_email, version)
        return False

    def archive_active_plan(self, user_email: str) -> bool:
        """Deletes singleton plan for user."""
        result = self.collection.delete_one({"user_email": user_email})
        return result.deleted_count > 0
