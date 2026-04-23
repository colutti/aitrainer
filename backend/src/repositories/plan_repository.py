"""Repository for singleton central plan."""

from datetime import datetime

import pymongo
from pymongo import ReturnDocument
from pymongo.database import Database

from src.api.models.plan import UserPlan
from src.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    """MongoDB repository for singleton user plan."""

    def __init__(self, database: Database):
        super().__init__(database, "plans")
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Ensure indexes required for singleton plan operations."""
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING)],
            name="user_email_idx",
        )

    def save_plan(self, plan: UserPlan) -> str:
        """Upserts singleton plan per user and returns its document id."""
        payload = plan.model_dump(exclude={"id"})
        payload["updated_at"] = datetime.now()

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

    def get_plan(self, user_email: str) -> UserPlan | None:
        """Returns singleton plan for user."""
        doc = self.collection.find_one(
            {"user_email": user_email},
            sort=[("updated_at", pymongo.DESCENDING)],
        )
        return UserPlan(**doc) if doc else None

    def get_latest_plan(self, user_email: str) -> UserPlan | None:
        """Returns singleton plan (same document)."""
        return self.get_plan(user_email)
