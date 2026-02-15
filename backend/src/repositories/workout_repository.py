"""
This module contains the repository for workout logs.
"""

from datetime import datetime, timedelta
from typing import Any
import pymongo
from bson import ObjectId
from pymongo.database import Database

from src.api.models.workout_log import WorkoutLog, WorkoutWithId
from src.api.models.workout_stats import WorkoutStats, PersonalRecord, VolumeStat
from src.repositories.base import BaseRepository


class WorkoutRepository(BaseRepository):
    """
    Repository for managing workout logs in MongoDB.
    """

    def __init__(self, database: Database):
        super().__init__(database, "workout_logs")

    def save_log(self, workout: WorkoutLog) -> str:
        """
        Saves a workout log to the database.
        """
        result = self.collection.insert_one(workout.model_dump())
        self.logger.info(
            "Workout log saved for user %s with %d exercises",
            workout.user_email,
            len(workout.exercises),
        )
        return str(result.inserted_id)

    def get_logs(self, user_email: str, limit: int = 50) -> list[WorkoutWithId]:
        """
        Retrieves the most recent workout logs for a user.
        """
        cursor = (
            self.collection.find({"user_email": user_email})
            .sort("date", pymongo.DESCENDING)
            .limit(limit)
        )
        workouts = []
        for doc in cursor:
            workouts.append(WorkoutWithId(**doc))

        self.logger.debug(
            "Retrieved %d workout logs for user: %s", len(workouts), user_email
        )
        return workouts

    def delete_log(self, workout_id: str) -> bool:
        """
        Deletes a workout log by its ID.
        """
        result = self.collection.delete_one({"_id": ObjectId(workout_id)})
        deleted = result.deleted_count > 0
        if deleted:
            self.logger.info("Workout log %s deleted", workout_id)
        else:
            self.logger.warning("Workout log %s not found for deletion", workout_id)
        return deleted

    def get_log_by_id(self, workout_id: str) -> dict | None:
        """
        Retrieves a single workout log by its ID.
        """
        return self.collection.find_one({"_id": ObjectId(workout_id)})

    def get_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
        workout_type: str | None = None,
    ) -> tuple[list[dict], int]:
        """
        Retrieves paginated workout logs for a user.
        """
        query: dict[str, Any] = {"user_email": user_email}
        if workout_type:
            query["workout_type"] = workout_type

        cursor, total = self.get_paginated_cursor(
            query=query, page=page, page_size=page_size
        )

        workouts = list(cursor)

        self.logger.debug(
            "Retrieved %d/%d workout logs for user: %s (page %d)",
            len(workouts),
            total,
            user_email,
            page,
        )
        return workouts, total

    def get_types(self, user_email: str) -> list[str]:
        """
        Retrieves all unique workout types for a user.
        """
        types = self.collection.distinct("workout_type", {"user_email": user_email})
        return sorted([t for t in types if t])

    def get_stats(self, user_email: str) -> WorkoutStats:
        """
        Calculates and retrieves comprehensive workout statistics for a user.
        """
        # 1. Get all workouts (projection for speed)
        cursor = self.collection.find(
            {"user_email": user_email},
            {
                "date": 1,
                "workout_type": 1,
                "exercises": 1,
                "user_email": 1,
                "duration_minutes": 1,
            },
        ).sort("date", pymongo.DESCENDING)

        all_workouts = list(cursor)
        if not all_workouts:
            return WorkoutStats(
                current_streak_weeks=0,
                weekly_frequency=[False] * 7,
                weekly_volume=[],
                recent_prs=[],
                total_workouts=0,
                last_workout=None,
            )

        # 2. Basic Metrics
        total_workouts = len(all_workouts)
        last_workout_doc = all_workouts[0]
        last_workout_doc["id"] = str(last_workout_doc.pop("_id"))
        last_workout = WorkoutWithId(**last_workout_doc)

        # 3. Calculated Metrics
        current_streak = self._calculate_weekly_streak(all_workouts)
        freq, volume = self._calculate_weekly_metrics(all_workouts)
        prs = self._calculate_recent_prs(all_workouts)
        vol_trend = self._calculate_volume_trend(all_workouts)
        strength_radar = self._calculate_strength_radar(all_workouts)

        return WorkoutStats(
            current_streak_weeks=current_streak,
            weekly_frequency=freq,
            weekly_volume=volume,
            recent_prs=prs,
            total_workouts=total_workouts,
            last_workout=last_workout,
            volume_trend=vol_trend,
            strength_radar=strength_radar,
        )

    # pylint: disable=too-many-locals
    def _calculate_weekly_streak(self, workouts: list[dict]) -> int:
        """Calculates the number of consecutive weeks with at least 3 workouts."""
        if not workouts:
            return 0

        weeks_data: dict[tuple[int, int], int] = {}
        for w in workouts:
            dt = w["date"]
            iso_year, iso_week, _ = dt.isocalendar()
            key = (iso_year, iso_week)
            weeks_data[key] = weeks_data.get(key, 0) + 1

        now = datetime.now()
        current_year, current_week, _ = now.isocalendar()

        streak = 0

        def met_criteria(y, w):
            return weeks_data.get((y, w), 0) >= 3

        check_year, check_week = current_year, current_week

        # If current week hasn't met criteria yet, but it's the CURRENT week,
        # we skip it and start counting from the previous week.
        if not met_criteria(check_year, check_week):
            prev_week_date = datetime.fromisocalendar(
                check_year, check_week, 1
            ) - timedelta(days=7)
            check_year, check_week, _ = prev_week_date.isocalendar()

        while met_criteria(check_year, check_week):
            streak += 1
            check_date = datetime.fromisocalendar(
                check_year, check_week, 1
            ) - timedelta(days=7)
            check_year, check_week, _ = check_date.isocalendar()

        return streak

    # pylint: disable=too-many-locals
    def _calculate_weekly_metrics(
        self, workouts: list[dict]
    ) -> tuple[list[bool], list[VolumeStat]]:
        """Calculates frequency and volume for the current week."""
        now = datetime.now()
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

        current_week_workouts = [w for w in workouts if w["date"] >= start_of_week]

        freq = [False] * 7
        for w in current_week_workouts:
            day_idx = w["date"].weekday()
            freq[day_idx] = True

        volume_map: dict[str, float] = {}
        for w in current_week_workouts:
            cat = w.get("workout_type", "Outros") or "Outros"
            exercises = w.get("exercises", [])
            for ex in exercises:
                reps_list = ex.get("reps_per_set", [])
                weights_list = ex.get("weights_per_set", [])

                vol = 0.0
                for i, reps in enumerate(reps_list):
                    weight = weights_list[i] if i < len(weights_list) else 0.0
                    vol += reps * weight

                volume_map[cat] = volume_map.get(cat, 0.0) + vol

        volume_stats = [
            VolumeStat(category=k, volume=round(v, 1)) for k, v in volume_map.items()
        ]
        volume_stats.sort(key=lambda x: x.volume, reverse=True)
        return freq, volume_stats

    # pylint: disable=too-many-locals
    def _calculate_recent_prs(
        self, workouts: list[dict], limit: int = 3
    ) -> list[PersonalRecord]:
        """Identifies recent personal records."""
        max_weights: dict[str, dict[str, Any]] = {}

        for w in reversed(workouts):
            w_id = str(w.get("_id"))
            dt = w["date"]
            exercises = w.get("exercises", [])

            for ex in exercises:
                name = ex.get("name")
                if not name:
                    continue

                weights = ex.get("weights_per_set", [])
                reps = ex.get("reps_per_set", [])

                if not weights:
                    continue

                # Skip cardio-only exercises (all weights are 0, but has distance/duration)
                if all(w == 0 for w in weights):
                    continue

                session_max = -1.0
                session_max_reps = 0

                for i, weight in enumerate(weights):
                    if weight > session_max:
                        session_max = weight
                        session_max_reps = reps[i] if i < len(reps) else 0

                if session_max >= 0:
                    current_record = max_weights.get(name)
                    if not current_record or session_max > current_record["weight"]:
                        max_weights[name] = {
                            "weight": session_max,
                            "reps": session_max_reps,
                            "date": dt,
                            "workout_id": w_id,
                        }

        prs_list = [
            PersonalRecord(
                exercise_name=name,
                weight=data["weight"],
                reps=data["reps"],
                date=data["date"],
                workout_id=data["workout_id"],
            )
            for name, data in max_weights.items()
        ]

        prs_list.sort(key=lambda x: x.date, reverse=True)
        return prs_list[:limit]

    def _calculate_volume_trend(self, workouts: list[dict]) -> list[float]:
        """Calculates weekly volume total for the last 8 weeks."""
        now = datetime.now()
        weeks: list[float] = [0.0] * 8

        for w in workouts:
            age_days = (now - w["date"]).days
            week_idx = age_days // 7
            if week_idx < 8:
                vol = 0.0
                for ex in w.get("exercises", []):
                    reps_list = ex.get("reps_per_set", [])
                    weights_list = ex.get("weights_per_set", [])
                    for i, r in enumerate(reps_list):
                        vol += r * (weights_list[i] if i < len(weights_list) else 0.0)
                weeks[week_idx] += vol

        # Return reversed to show chronological order in chart
        return [round(v, 1) for v in reversed(weeks)]

    # pylint: disable=too-many-locals
    def _calculate_strength_radar(self, workouts: list[dict]) -> dict[str, float]:
        """Calculates current vs peak strength ratio (0-1.0) for major muscle groups."""
        categories = {
            "Push": ["Supino", "Peito", "Ombro", "Tríceps", "Militar", "Bench"],
            "Pull": [
                "Costas", "Remada", "Puxada", "Bíceps", "Levantamento Terra",
                "Deadlift", "Row",
            ],
            "Legs": [
                "Agachamento", "Leg Press", "Extensora", "Flexora", "Pernas",
                "Panturrilha", "Squat",
            ],
        }

        peak_strength: dict[str, float] = {}
        current_strength: dict[str, float] = {}

        # Sort by date to find latest
        sorted_workouts = sorted(workouts, key=lambda x: x["date"])

        for w in sorted_workouts:
            for ex in w.get("exercises", []):
                name = ex.get("name", "")
                cat = next(
                    (
                        k
                        for k, v in categories.items()
                        if any(term.lower() in name.lower() for term in v)
                    ),
                    "Outros",
                )
                if cat == "Outros":
                    continue

                weights = ex.get("weights_per_set", [])
                if not weights:
                    continue
                # We skip bodyweight exercises (0 weight) for strength radar
                valid_weights = [weight for weight in weights if weight > 0]
                if not valid_weights:
                    continue

                max_w = max(valid_weights)
                peak_strength[cat] = max(peak_strength.get(cat, 0), max_w)
                current_strength[cat] = max_w  # Latest session max

        # Return ratio of current / peak (0 to 1.0)
        result = {}
        for cat in categories:
            peak = peak_strength.get(cat, 0)
            curr = current_strength.get(cat, 0)
            result[cat] = round(curr / peak if peak > 0 else 0, 2)

        return result
