"""
This module contains the repository for weight logs.
"""

from datetime import datetime, date
import pymongo
from pymongo.database import Database

from src.api.models.weight_log import WeightLog
from src.repositories.base import BaseRepository


class WeightRepository(BaseRepository):
    """
    Repository for managing weight and body composition logs in MongoDB.
    """

    def __init__(self, database: Database):
        super().__init__(database, "weight_logs")

    def ensure_indexes(self) -> None:
        """
        Ensures unique indexes for weight logs (one per day per user).
        """
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING), ("date", pymongo.ASCENDING)],
            unique=True,
            name="unique_daily_weight_log",
        )
        self.logger.info("Weight logs unique daily index ensured.")

    def save_log(self, log: WeightLog) -> tuple[str, bool]:
        """
        Saves or updates a weight log.
        """
        # pylint: disable=duplicate-code
        log_datetime = datetime(log.date.year, log.date.month, log.date.day)

        data = log.model_dump(exclude_none=True)
        data["date"] = log_datetime

        result = self.collection.update_one(
            {"user_email": log.user_email, "date": log_datetime},
            {"$set": data},
            upsert=True,
        )

        is_new = result.upserted_id is not None

        if is_new:
            doc_id = str(result.upserted_id)
            self.logger.info(
                "Created new weight log for %s on %s", log.user_email, log.date
            )
        else:
            existing = self.collection.find_one(
                {"user_email": log.user_email, "date": log_datetime}
            )
            doc_id = str(existing["_id"]) if existing else ""
            self.logger.info(
                "Updated existing weight log for %s on %s", log.user_email, log.date
            )

        return doc_id, is_new

    def delete_log(self, user_email: str, log_date: date) -> bool:
        """
        Deletes a weight log for a specific date.
        """
        query_date = datetime(log_date.year, log_date.month, log_date.day)

        result = self.collection.delete_one(
            {"user_email": user_email, "date": query_date}
        )

        if result.deleted_count > 0:
            self.logger.info("Deleted weight log for %s on %s", user_email, log_date)
            return True

        self.logger.warning(
            "Attempted to delete non-existent weight log for %s on %s",
            user_email,
            log_date,
        )
        return False

    def get_logs(self, user_email: str, limit: int = 30) -> list[WeightLog]:
        """
        Retrieves the most recent weight logs for a user.
        """
        cursor = (
            self.collection.find({"user_email": user_email})
            .sort("date", pymongo.DESCENDING)
            .limit(limit)
        )

        logs = []
        for doc in cursor:
            if isinstance(doc["date"], datetime):
                doc["date"] = doc["date"].date()
            if "_id" in doc:
                del doc["_id"]
            logs.append(WeightLog(**doc))

        return logs

    def get_logs_by_date_range(
        self, user_email: str, start_date: date, end_date: date
    ) -> list[WeightLog]:
        """
        Retrieves weight logs within a specific date range.
        """
        start = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)

        cursor = self.collection.find(
            {"user_email": user_email, "date": {"$gte": start, "$lte": end}}
        ).sort("date", pymongo.ASCENDING)

        logs = []
        for doc in cursor:
            if isinstance(doc["date"], datetime):
                doc["date"] = doc["date"].date()
            if "_id" in doc:
                del doc["_id"]
            logs.append(WeightLog(**doc))

        return logs

    def get_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[dict], int]:
        """
        Retrieves paginated weight logs.
        """
        query = {"user_email": user_email}

        total = self.collection.count_documents(query)
        skip = (page - 1) * page_size

        cursor = (
            self.collection.find(query)
            .sort("date", pymongo.DESCENDING)
            .skip(skip)
            .limit(page_size)
        )

        logs = []
        for doc in cursor:
            if isinstance(doc.get("date"), datetime):
                doc["date"] = doc["date"].date()
            if "_id" in doc:
                doc["id"] = str(doc.pop("_id"))
            logs.append(doc)

        return logs, total
