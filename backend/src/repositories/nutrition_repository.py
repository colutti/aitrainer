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
        self.ensure_query_indexes()

    def ensure_query_indexes(self) -> None:
        """Ensures indexes used by frequent nutrition reads."""
        self.collection.create_index(
            [("user_email", pymongo.ASCENDING), ("date", pymongo.DESCENDING)],
            name="nutrition_user_date_idx",
        )
        self.logger.info("Nutrition query indexes ensured.")

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

        query = {"user_email": log.user_email, "date": log_date}
        data = log.model_dump(exclude_none=True)
        return self.upsert_document(query, data, f"nutrition log (date: {log_date})")

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

    def _get_today_log(self, now: datetime, logs: list[dict]) -> NutritionWithId | None:
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_log_doc = next(
            (log_item for log_item in logs if log_item["date"] >= start_of_today), None
        )
        if not today_log_doc:
            return None

        doc_copy = dict(today_log_doc)
        doc_copy["id"] = str(doc_copy.get("_id"))
        if "_id" in doc_copy:
            del doc_copy["_id"]
        return NutritionWithId(**doc_copy)

    def _get_last_14_days_stats(
        self, now: datetime, logs: list[dict]
    ) -> list[DailyMacros]:
        stats = []
        for i in range(14):
            date_item = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            log = next(
                (log_item for log_item in logs if log_item["date"] == date_item), None
            )
            if log:
                stats.append(
                    DailyMacros(
                        date=date_item,
                        calories=log["calories"],
                        protein=log["protein_grams"],
                        carbs=log["carbs_grams"],
                        fat=log["fat_grams"],
                    )
                )
            else:
                stats.append(
                    DailyMacros(date=date_item, calories=0, protein=0, carbs=0, fat=0)
                )
        stats.sort(key=lambda x: x.date)
        return stats

    def _get_weekly_adherence(self, now: datetime, logs: list[dict]) -> list[bool]:
        current_week_start = now - timedelta(days=now.weekday())
        current_week_start = current_week_start.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        adherence = [False] * 7
        for log_entry in logs:
            if log_entry["date"] >= current_week_start:
                day_idx = log_entry["date"].weekday()
                adherence[day_idx] = True
        return adherence

    def _get_recent_averages(
        self, now: datetime, logs: list[dict], days: int
    ) -> tuple[float, float]:
        start_date = (now - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        recent_logs = [log_item for log_item in logs if log_item["date"] >= start_date]
        count = len(recent_logs)
        avg_cal = (
            sum(log_item["calories"] for log_item in recent_logs) / count
            if count > 0
            else 0.0
        )
        avg_prot = (
            sum(log_item["protein_grams"] for log_item in recent_logs) / count
            if count > 0
            else 0.0
        )
        return avg_cal, avg_prot

    def _get_tdee_stats(self, user_email: str, tdee_service) -> dict:
        if not tdee_service:
            self.logger.debug("TDEE service not provided for stats calculation")
            return {}
        try:
            return tdee_service.calculate_tdee(user_email)
        except (ValueError, TypeError, AttributeError, RuntimeError) as e:
            self.logger.warning("Failed to calculate Adaptive TDEE for stats: %s", e)
            return {}

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

        today_log = self._get_today_log(now, logs)
        last_14_days_stats = self._get_last_14_days_stats(now, logs)
        weekly_adherence = self._get_weekly_adherence(now, logs)
        avg_cal, avg_prot = self._get_recent_averages(now, logs, 7)
        avg_cal_14, _ = self._get_recent_averages(now, logs, 14)

        total_logs = self.collection.count_documents({"user_email": user_email})
        period_stats = self._get_tdee_stats(user_email, tdee_service)

        return NutritionStats(
            today=today_log,
            weekly_adherence=weekly_adherence,
            last_7_days=last_14_days_stats[-7:],
            last_14_days=last_14_days_stats,
            avg_daily_calories=round(avg_cal, 1),
            avg_daily_calories_14_days=round(avg_cal_14, 1),
            avg_protein=round(avg_prot, 1),
            total_logs=total_logs,
            tdee=period_stats.get("tdee"),
            daily_target=period_stats.get("daily_target"),
            macro_targets=period_stats.get("macro_targets"),
            stability_score=period_stats.get("stability_score"),
        )
