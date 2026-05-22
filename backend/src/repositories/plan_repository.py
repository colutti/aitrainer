"""Repository for the singleton plan and discovery draft."""

from datetime import datetime

import pymongo
from pymongo import ReturnDocument
from pymongo.database import Database

from pydantic import ValidationError

from src.api.models.plan import PlanDiscoveryState, UserPlan
from src.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    """MongoDB repository for singleton user plan."""

    def __init__(self, database: Database):
        super().__init__(database, "plans")
        self.discovery_collection = database["plan_discovery_states"]
        self.ensure_indexes()

    def ensure_indexes(self) -> None:
        """Ensure indexes required for singleton plan operations."""
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING)],
            name="user_email_idx",
        )
        self.discovery_collection.create_index(
            [("user_email", pymongo.ASCENDING)],
            name="plan_discovery_user_email_idx",
            unique=True,
        )

    def save_plan(self, plan: UserPlan) -> str:
        """Upserts singleton plan per user and returns its document id."""
        payload = plan.model_dump(mode="json", exclude={"id"})
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

    def partial_update_plan(self, user_email: str, updates: dict) -> str:
        """Updates specific fields of the singleton plan using native MongoDB $set."""
        updates["updated_at"] = datetime.now()
        doc = self.collection.find_one_and_update(
            {"user_email": user_email},
            {"$set": updates},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            return ""
        self.collection.delete_many(
            {"user_email": user_email, "_id": {"$ne": doc["_id"]}}
        )
        return str(doc["_id"])

    def get_plan(self, user_email: str) -> UserPlan | None:
        """Returns singleton plan for user."""
        doc = self.collection.find_one(
            {"user_email": user_email},
            sort=[("updated_at", pymongo.DESCENDING)],
        )
        if not doc:
            return None
        try:
            return UserPlan(**doc)
        except ValidationError as exc:
            self.logger.warning(
                "Invalid plan document for user %s: %s", user_email, exc,
            )
            return None

    def get_latest_plan(self, user_email: str) -> UserPlan | None:
        """Returns singleton plan (same document)."""
        return self.get_plan(user_email)

    def save_discovery(self, discovery: PlanDiscoveryState) -> str:
        """Upserts discovery draft per user and returns its document id."""
        payload = discovery.model_dump(mode="json", exclude={"id"})
        payload["updated_at"] = datetime.now()

        doc = self.discovery_collection.find_one_and_update(
            {"user_email": discovery.user_email},
            {"$set": payload},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        if doc is None:
            return ""
        return str(doc["_id"])

    def get_discovery(self, user_email: str) -> PlanDiscoveryState | None:
        """Returns the discovery draft for the user."""
        doc = self.discovery_collection.find_one({"user_email": user_email})
        if not doc:
            return None
        try:
            return PlanDiscoveryState(**doc)
        except ValidationError as exc:
            self.logger.warning(
                "Invalid plan discovery document for user %s: %s",
                user_email,
                exc,
            )
            return None

    def clear_discovery(self, user_email: str) -> None:
        """Deletes the discovery draft once a plan becomes active."""
        self.discovery_collection.delete_one({"user_email": user_email})
