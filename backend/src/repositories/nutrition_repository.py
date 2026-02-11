"""
This module contains the repository for nutrition logs.
"""

from datetime import datetime, timedelta, date as py_date
from typing import Any
import pymongo
from bson import ObjectId
from pymongo.database import Database

from src.api.models.nutrition_log import NutritionLog, NutritionWithId
from src.api.models.nutrition_stats import NutritionStats, DailyMacros
from src.repositories.base import BaseRepository


class NutritionRepository(BaseRepository):
    """
    Repository for managing nutrition logs in MongoDB.
    """

    def __init__(self, database: Database):
        super().__init__(database, "nutrition_logs")

    def ensure_indexes(self) -> None:
        """
        Ensures unique indexes for nutrition logs (one per day per user).
        """
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING), ("date", pymongo.ASCENDING)],
            unique=True,
            name="unique_daily_log",
        )
        self.logger.info("Nutrition logs unique daily index ensured.")

    def save_log(self, log: NutritionLog) -> tuple[str, bool]:
        """
        Saves or updates a nutrition log.
        """
        log_date = log.date
        if isinstance(log_date, py_date) and not isinstance(log_date, datetime):
            log_date = datetime.combine(log_date, datetime.min.time())

        log_date = log_date.replace(hour=0, minute=0, second=0, microsecond=0)
        log.date = log_date

        result = self.collection.update_one(
            {"user_email": log.user_email, "date": log_date},
            {"$set": log.model_dump()},
            upsert=True,
        )

        is_new = result.upserted_id is not None

        if is_new:
            doc_id = str(result.upserted_id)
            self.logger.info(
                "Created new nutrition log for %s on %s", log.user_email, log_date
            )
        else:
            existing = self.collection.find_one(
                {"user_email": log.user_email, "date": log_date}
            )
            doc_id = str(existing["_id"]) if existing else ""
            self.logger.info(
                "Updated existing nutrition log for %s on %s", log.user_email, log_date
            )

        return doc_id, is_new

    def get_logs(self, user_email: str, limit: int = 30) -> list[NutritionLog]:
        """
        Retrieves the most recent nutrition logs for a user.
        """
        cursor = (
            self.collection.find({"user_email": user_email})
            .sort("date", pymongo.DESCENDING)
            .limit(limit)
        )
        return [NutritionLog(**doc) for doc in cursor]

    def delete_log(self, log_id: str) -> bool:
        """
        Deletes a nutrition log by its ID.
        """
        result = self.collection.delete_one({"_id": ObjectId(log_id)})
        deleted = result.deleted_count > 0
        if deleted:
            self.logger.info("Nutrition log %s deleted", log_id)
        else:
            self.logger.warning("Nutrition log %s not found for deletion", log_id)
        return deleted

    def get_log_by_id(self, log_id: str) -> dict | None:
        """
        Retrieves a single nutrition log by its ID.
        """
        return self.collection.find_one({"_id": ObjectId(log_id)})

    def get_logs_by_date_range(
        self, user_email: str, start_date: datetime, end_date: datetime
    ) -> list[NutritionLog]:
        """
        Retrieves nutrition logs within a specific date range.
        """
        start = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        cursor = self.collection.find(
            {"user_email": user_email, "date": {"$gte": start, "$lte": end}}
        ).sort("date", pymongo.ASCENDING)

        return [NutritionLog(**doc) for doc in cursor]

    def get_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
        days: int | None = None,
    ) -> tuple[list[dict], int]:
        """
        Retrieves paginated nutrition logs.
        """
        query: dict[str, Any] = {"user_email": user_email}
        if days:
            start_date = datetime.now() - timedelta(days=days)
            query["date"] = {"$gte": start_date}

        cursor, total = self.get_paginated_cursor(
            query=query, page=page, page_size=page_size
        )

        logs = []
        for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            logs.append(doc)

        return logs, total

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def get_stats(self, user_email: str, tdee_service=None) -> NutritionStats:
        """
        Calculates and retrieves comprehensive nutrition statistics for a user.
        """
        now = datetime.now()
        start_date = now - timedelta(days=30)

        cursor = self.collection.find(
            {"user_email": user_email, "date": {"$gte": start_date}}
        ).sort("date", pymongo.DESCENDING)

        logs = list(cursor)

        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_log_doc = next(
            (log_item for log_item in logs if log_item["date"] >= start_of_today), None
        )
        today_log = None
        if today_log_doc:
            today_log_doc["id"] = str(today_log_doc.get("_id"))
            if "_id" in today_log_doc:
                del today_log_doc["_id"]
            today_log = NutritionWithId(**today_log_doc)

        last_14_days_stats = []
        for i in range(14):
            date_item = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            log = next((log_item for log_item in logs if log_item["date"] == date_item), None)
            if log:
                last_14_days_stats.append(
                    DailyMacros(
                        date=date_item,
                        calories=log["calories"],
                        protein=log["protein_grams"],
                        carbs=log["carbs_grams"],
                        fat=log["fat_grams"],
                    )
                )
            else:
                last_14_days_stats.append(
                    DailyMacros(date=date_item, calories=0, protein=0, carbs=0, fat=0)
                )
        last_14_days_stats.sort(key=lambda x: x.date)

        current_week_start = now - timedelta(days=now.weekday())
        current_week_start = current_week_start.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        weekly_adherence = [False] * 7
        for log_entry in logs:
            if log_entry["date"] >= current_week_start:
                day_idx = log_entry["date"].weekday()
                weekly_adherence[day_idx] = True

        recent_logs = [
            log_item
            for log_item in logs
            if log_item["date"]
            >= (now - timedelta(days=7)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        ]
        count = len(recent_logs)
        avg_cal = (
            sum(log_item["calories"] for log_item in recent_logs) / count
            if count > 0
            else 0
        )
        avg_prot = (
            sum(log_item["protein_grams"] for log_item in recent_logs) / count
            if count > 0
            else 0
        )

        recent_logs_14 = [
            log_item
            for log_item in logs
            if log_item["date"]
            >= (now - timedelta(days=14)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        ]
        count_14 = len(recent_logs_14)
        avg_cal_14 = (
            sum(log_item["calories"] for log_item in recent_logs_14) / count_14
            if count_14 > 0
            else 0
        )

        total_logs = self.collection.count_documents({"user_email": user_email})

        tdee_val = None
        target_val = None
        macro_targets = None
        stability_score = None

        if tdee_service:
            try:
                period_stats = tdee_service.calculate_tdee(user_email)
                tdee_val = period_stats.get("tdee")
                target_val = period_stats.get("daily_target")
                macro_targets = period_stats.get("macro_targets")
                stability_score = period_stats.get("stability_score")
            except Exception as e: # pylint: disable=broad-exception-caught
                self.logger.warning(
                    "Failed to calculate Adaptive TDEE for stats: %s", e
                )
        else:
            self.logger.debug("TDEE service not provided for stats calculation")

        return NutritionStats(
            today=today_log,
            weekly_adherence=weekly_adherence,
            last_7_days=last_14_days_stats[-7:],
            last_14_days=last_14_days_stats,
            avg_daily_calories=round(avg_cal, 1),
            avg_daily_calories_14_days=round(avg_cal_14, 1),
            avg_protein=round(avg_prot, 1),
            total_logs=total_logs,
            tdee=tdee_val,
            daily_target=target_val,
            macro_targets=macro_targets,
            stability_score=stability_score,
        )
