from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
from unittest.mock import patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    NutritionDailyTargets,
    PlanAlignment,
    PlanGoal,
    PlanNutrition,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    PlanTraining,
    TrainingExercise,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.api.models.nutrition_log import NutritionLog
from src.api.models.weight_log import WeightLog
from src.api.models.workout_log import ExerciseLog, WorkoutLog
from src.repositories.plan_repository import PlanRepository
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.weight_repository import WeightRepository
from src.repositories.workout_repository import WorkoutRepository
from src.services.auth import verify_token


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeReplaceResult:
    def __init__(self, matched_count: int) -> None:
        self.matched_count = matched_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, field: str, direction: int) -> "FakeCursor":
        reverse = direction < 0
        self._docs.sort(key=lambda doc: doc.get(field), reverse=reverse)
        return self

    def skip(self, amount: int) -> "FakeCursor":
        self._docs = self._docs[amount:]
        return self

    def limit(self, amount: int) -> "FakeCursor":
        self._docs = self._docs[:amount]
        return self

    def __iter__(self):
        return iter([deepcopy(doc) for doc in self._docs])


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, value in query.items():
            current = doc.get(key)
            if isinstance(value, dict):
                if "$ne" in value and current == value["$ne"]:
                    return False
                if "$gte" in value and current < value["$gte"]:
                    return False
                if "$lte" in value and current > value["$lte"]:
                    return False
                continue
            if current != value:
                return False
        return True

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> FakeUpdateResult:
        for doc in self.docs:
            if self._matches(doc, query):
                original = deepcopy(doc)
                for key, value in update.get("$set", {}).items():
                    doc[key] = deepcopy(value)
                for key in update.get("$unset", {}):
                    doc.pop(key, None)
                return FakeUpdateResult(modified_count=0 if doc == original else 1)

        if upsert:
            inserted_id = ObjectId()
            self.docs.append(
                {
                    "_id": inserted_id,
                    **deepcopy(query),
                    **deepcopy(update.get("$set", {})),
                }
            )
            return FakeUpdateResult(upserted_id=inserted_id, modified_count=0)

        return FakeUpdateResult(modified_count=0)

    def insert_one(self, data: dict) -> FakeInsertResult:
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(data)})
        return FakeInsertResult(inserted_id)

    def replace_one(self, query: dict, data: dict) -> FakeReplaceResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs[index] = {"_id": doc["_id"], **deepcopy(data)}
                return FakeReplaceResult(matched_count=1)
        return FakeReplaceResult(matched_count=0)

    def find_one_and_update(
        self,
        query: dict,
        update: dict,
        upsert: bool = False,
        return_document=None,
    ) -> dict | None:
        result = self.update_one(query, update, upsert=upsert)
        if result.upserted_id is not None:
            return self.find_one({"_id": result.upserted_id})
        return self.find_one(query)

    def find_one(self, query: dict, projection: dict | None = None, sort=None) -> dict | None:
        docs = [doc for doc in self.docs if self._matches(doc, query)]
        if sort:
            field, direction = sort[0]
            docs.sort(key=lambda doc: doc.get(field), reverse=direction < 0)
        if not docs:
            return None
        doc = deepcopy(docs[0])
        if projection:
            keep = {key for key, value in projection.items() if value}
            if keep:
                doc = {
                    key: value for key, value in doc.items() if key in keep or key == "_id"
                }
        return doc

    def find(self, query: dict, projection: dict | None = None) -> FakeCursor:
        docs = [deepcopy(doc) for doc in self.docs if self._matches(doc, query)]
        if projection:
            keep = {key for key, value in projection.items() if value}
            if keep:
                docs = [
                    {key: value for key, value in doc.items() if key in keep or key == "_id"}
                    for doc in docs
                ]
        return FakeCursor(docs)

    def delete_one(self, query: dict) -> FakeDeleteResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[index]
                return FakeDeleteResult(deleted_count=1)
        return FakeDeleteResult(deleted_count=0)

    def count_documents(self, query: dict) -> int:
        return len([doc for doc in self.docs if self._matches(doc, query)])


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulDashboardDb:
    def __init__(self) -> None:
        self.database = FakeDatabase()
        self.plans = PlanRepository(self.database)
        self.weight = WeightRepository(self.database)
        self.nutrition = NutritionRepository(self.database)
        self.workouts_repo = WorkoutRepository(self.database)

    def save_workout_log(self, workout):
        return self.workouts_repo.save_log(workout)

    def get_workout_by_id(self, workout_id: str):
        return self.workouts_repo.get_log_by_id(workout_id)

    def get_workout_logs(self, user_email: str, limit: int = 30):
        return self.workouts_repo.get_logs(user_email, limit)

    def get_nutrition_by_id(self, log_id: str):
        return self.nutrition.get_log_by_id(log_id)

    def save_nutrition_log(self, log):
        return self.nutrition.save_log(log)

    def get_nutrition_logs_by_date_range(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ):
        return self.nutrition.get_logs_by_date_range(user_email, start_date, end_date)

    def get_nutrition_logs(self, user_email: str, limit: int = 10):
        return self.nutrition.get_logs(user_email, limit)

    def get_weight_logs(self, user_email: str, limit: int = 30):
        return self.weight.get_logs(user_email, limit)

    def get_weight_logs_by_date_range(self, user_email: str, start_date: date, end_date: date):
        return self.weight.get_logs_by_date_range(user_email, start_date, end_date)

    def get_user_profile(self, _email: str):
        return None


def _build_active_plan(user_email: str) -> UserPlan:
    return UserPlan(
        user_email=user_email,
        title="Cutting com macros do plano",
        goal=PlanGoal(
            primary_goal="fat_loss",
            outcome_summary="Perder gordura sem sacrificar massa magra",
            success_metrics=[
                SuccessMetric(
                    metric_name="peso",
                    target_value=78.0,
                    unit="kg",
                    direction="decrease",
                )
            ],
        ),
        timeline=PlanTimeline(
            start_date=date(2026, 6, 1),
            target_date=date(2026, 8, 1),
            review_cadence_days=14,
            current_phase="base",
        ),
        user_context=PlanUserContext(
            training_days_available=["monday", "wednesday", "friday"],
            session_duration_min=60,
            constraints=["nenhuma"],
            preferences=["manter consistencia"],
            available_equipment=["barbell", "dumbbells"],
            training_level="intermediate",
            nutrition_preferences=["high protein"],
        ),
        training=PlanTraining(
            split_name="Upper/Lower/Full",
            frequency_per_week=3,
            session_duration_min=60,
            routines=[
                TrainingRoutine(
                    id="full-body-a",
                    name="Full Body A",
                    objective="manter volume base",
                    exercises=[
                        TrainingExercise(
                            name="Bench Press",
                            sets=3,
                            rep_range=RepRange(min_reps=6, max_reps=8),
                            intensity=IntensityPrescription(
                                prescription_type="rpe",
                                target="7",
                            ),
                            progression_rule=ProgressionRule(
                                method="double_progression",
                                increase_when="bater topo da faixa em todas as series",
                                hold_when="manter tecnica",
                                deload_when="2 semanas sem progresso",
                            ),
                        )
                    ],
                )
            ],
            weekly_schedule=[
                WeeklyScheduleItem(
                    day="monday",
                    routine_id="full-body-a",
                    focus="forca",
                ),
                WeeklyScheduleItem(
                    day="wednesday",
                    routine_id="full-body-a",
                    focus="volume",
                ),
                WeeklyScheduleItem(
                    day="friday",
                    routine_id="full-body-a",
                    focus="densidade",
                ),
            ],
        ),
        nutrition=PlanNutrition(
            daily_targets=NutritionDailyTargets(
                calories_kcal=2500,
                protein_g=180,
                carbs_g=260,
                fat_g=72,
            ),
            strategy="cutting com proteina alta",
            adherence_target_pct=90,
        ),
        alignment=PlanAlignment(
            training_nutrition_rationale="Volume suficiente com deficit controlado",
            energy_strategy="deficit",
            conflict_rules=[
                ConflictRule(
                    trigger="queda forte de performance",
                    action="reduzir deficit",
                )
            ],
        ),
        tracking=PlanTracking(
            workout_adherence_target_pct=85,
            nutrition_adherence_target_pct=90,
            progress_markers=[
                ProgressMarker(
                    name="peso",
                    source="body",
                    target_summary="reduzir peso semanalmente de forma consistente",
                )
            ],
            review_questions=["O deficit continua sustentavel?"],
        ),
    )


def test_dashboard_aggregates_stateful_weight_nutrition_and_workouts():
    user_email = "dashboard@example.com"
    db = StatefulDashboardDb()
    today = datetime(2026, 6, 27, 12, 0, 0)
    week_start = (today - timedelta(days=today.weekday())).replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0,
    )

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return today.astimezone(tz)
            return today

    class FakeAdaptiveTDEE:
        def __init__(self, _db) -> None:
            self._db = _db

        def calculate_tdee(self, _user_email: str, lookback_weeks: int = 3):
            assert lookback_weeks == 3
            return {
                "tdee": 2400,
                "daily_target": 2200,
                "confidence": "high",
                "weight_change_per_week": -0.2,
                "energy_balance": -150.0,
                "status": "cutting",
                "goal_type": "lose",
                "consistency_score": 82,
                "stability_score": 74,
                "macro_targets": {
                    "protein": 160,
                    "carbs": 210,
                    "fat": 65,
                },
            }

        def calculate_ema_trend(self, current_value: float, previous_value: float | None):
            if previous_value is None:
                return current_value
            return round((previous_value * 0.8) + (current_value * 0.2), 2)

    app.dependency_overrides[verify_token] = lambda: user_email

    from src.core.deps import get_mongo_database
    from src.api.endpoints.dashboard import get_mongo_database as get_dashboard_mongo_database

    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_dashboard_mongo_database] = lambda: db

    try:
        _older_weight_id, older_is_new = db.weight.save_log(
            WeightLog(
                user_email=user_email,
                date=date(2026, 6, 20),
                weight_kg=80.0,
                trend_weight=79.8,
                body_fat_pct=18.0,
                muscle_mass_pct=40.0,
                muscle_mass_kg=32.0,
                bmr=1800,
                source="manual",
                notes="older weight",
            )
        )
        assert older_is_new is True

        _current_weight_id, current_is_new = db.weight.save_log(
            WeightLog(
                user_email=user_email,
                date=date(2026, 6, 27),
                weight_kg=79.5,
                trend_weight=79.74,
                body_fat_pct=17.2,
                muscle_mass_pct=40.8,
                muscle_mass_kg=32.5,
                bmr=1810,
                source="manual",
                notes="current weight",
            )
        )
        assert current_is_new is True

        _nutrition_id, nutrition_is_new = db.nutrition.save_log(
            NutritionLog(
                user_email=user_email,
                date=datetime(2026, 6, 27, 8, 0, 0),
                source="manual",
                calories=2100,
                protein_grams=150.0,
                carbs_grams=205.0,
                fat_grams=63.0,
                fiber_grams=28.0,
                notes="dashboard meal",
                partial_logged=False,
            )
        )
        assert nutrition_is_new is True

        _workout_one_id = db.workouts_repo.save_log(
            WorkoutLog(
                user_email=user_email,
                date=week_start,
                workout_type="Push Day",
                duration_minutes=55,
                source="manual",
                external_id="push-100",
                exercises=[
                    ExerciseLog(
                        name="Bench Press",
                        sets=2,
                        reps_per_set=[10, 8],
                        weights_per_set=[60.0, 70.0],
                    )
                ],
            )
        )
        workout_two_id = db.workouts_repo.save_log(
            WorkoutLog(
                user_email=user_email,
                date=week_start + timedelta(days=1),
                workout_type="Pull Day",
                duration_minutes=60,
                source="manual",
                external_id="pull-100",
                exercises=[
                    ExerciseLog(
                        name="Deadlift",
                        sets=2,
                        reps_per_set=[5, 5],
                        weights_per_set=[100.0, 110.0],
                    )
                ],
            )
        )
        _workout_three_id = db.workouts_repo.save_log(
            WorkoutLog(
                user_email=user_email,
                date=week_start + timedelta(days=2),
                workout_type="Leg Day",
                duration_minutes=70,
                source="manual",
                external_id="legs-100",
                exercises=[
                    ExerciseLog(
                        name="Squat",
                        sets=2,
                        reps_per_set=[5, 5],
                        weights_per_set=[120.0, 125.0],
                    )
                ],
            )
        )

        with (
            patch("src.api.endpoints.dashboard._get_today", return_value=today),
            patch("src.api.endpoints.dashboard.AdaptiveTDEEService", FakeAdaptiveTDEE),
            patch("src.repositories.workout_repository.datetime", FrozenDateTime),
        ):
            dashboard_response = client.get("/dashboard")

        assert dashboard_response.status_code == 200
        payload = dashboard_response.json()

        assert payload["stats"]["metabolism"] == {
            "tdee": 2400,
            "daily_target": 2200,
            "confidence": "high",
            "weekly_change": -0.2,
            "energy_balance": -150.0,
            "status": "cutting",
                "macro_targets": {
                    "protein": 160,
                    "carbs": 210,
                    "fat": 65,
                },
                "macro_source": "fallback",
                "goal_type": "lose",
            "consistency_score": 82,
            "stability_score": 74,
        }

        assert payload["stats"]["calories"] == {
            "consumed": 2100.0,
            "target": 2200.0,
            "percent": 95.5,
        }

        assert payload["stats"]["workouts"]["completed"] == 3
        assert payload["stats"]["workouts"]["target"] == 4
        assert payload["stats"]["workouts"]["lastWorkoutDate"] == "2026-06-24 09:00:00"

        assert payload["stats"]["body"]["weight_current"] == 79.5
        assert payload["stats"]["body"]["weight_diff"] == -0.5
        assert payload["stats"]["body"]["weight_trend"] == "down"
        assert payload["stats"]["body"]["body_fat_pct"] == 17.2
        assert payload["stats"]["body"]["muscle_mass_pct"] == 40.8
        assert payload["stats"]["body"]["muscle_mass_kg"] == 32.5
        assert payload["stats"]["body"]["bmr"] == 1810.0

        assert payload["weightHistory"] == [
            {"date": "2026-06-20", "weight": 80.0},
            {"date": "2026-06-27", "weight": 79.5},
        ]
        assert payload["weightTrend"] == [
            {"date": "2026-06-20", "value": 79.8},
            {"date": "2026-06-27", "value": 79.74},
        ]

        assert payload["streak"]["current_weeks"] == 1
        assert payload["streak"]["last_activity_date"] == "2026-06-24 09:00:00"
        assert payload["recentPRs"][0]["exercise"] == "Squat"
        assert payload["recentPRs"][1]["exercise"] == "Deadlift"
        assert payload["recentPRs"][1]["id"] == f"{workout_two_id}_Deadlift"
        assert payload["strengthRadar"] == {
            "push": 1.0,
            "pull": 1.0,
            "legs": 1.0,
            "core": 0.0,
        }
        assert payload["weeklyFrequency"] == [True, True, True, False, False, False, False]
        assert payload["volumeTrend"][-1] == 3435.0

        assert len(payload["recentActivities"]) == 5
        assert payload["recentActivities"][0]["type"] == "nutrition"
        assert {item["type"] for item in payload["recentActivities"]} == {
            "workout",
            "nutrition",
            "body",
        }
    finally:
        app.dependency_overrides.clear()


def test_dashboard_prefers_active_plan_macros_over_tdee_macros():
    user_email = "dashboard-plan@example.com"
    db = StatefulDashboardDb()
    today = datetime(2026, 6, 27, 12, 0, 0)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return today.astimezone(tz)
            return today

    class FakeAdaptiveTDEE:
        def __init__(self, _db) -> None:
            self._db = _db

        def calculate_tdee(self, _user_email: str, lookback_weeks: int = 3):
            assert lookback_weeks == 3
            return {
                "tdee": 2480,
                "daily_target": 2240,
                "confidence": "high",
                "weight_change_per_week": -0.15,
                "energy_balance": -120.0,
                "status": "cutting",
                "goal_type": "lose",
                "consistency_score": 88,
                "stability_score": 79,
                "macro_targets": {
                    "protein": 155,
                    "carbs": 205,
                    "fat": 60,
                },
            }

        def calculate_ema_trend(self, current_value: float, previous_value: float | None):
            if previous_value is None:
                return current_value
            return round((previous_value * 0.8) + (current_value * 0.2), 2)

    active_plan = _build_active_plan(user_email)
    db.plans.save_plan(active_plan)

    app.dependency_overrides[verify_token] = lambda: user_email
    from src.core.deps import get_mongo_database
    from src.api.endpoints.dashboard import get_mongo_database as get_dashboard_mongo_database

    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_dashboard_mongo_database] = lambda: db

    try:
        with (
            patch("src.api.endpoints.dashboard._get_today", return_value=today),
            patch("src.api.endpoints.dashboard.AdaptiveTDEEService", FakeAdaptiveTDEE),
            patch("src.repositories.workout_repository.datetime", FrozenDateTime),
        ):
            dashboard_response = client.get("/dashboard")

        assert dashboard_response.status_code == 200
        payload = dashboard_response.json()

        assert payload["stats"]["metabolism"]["macro_targets"] == {
            "protein": 180,
            "carbs": 260,
            "fat": 72,
        }
        assert payload["stats"]["metabolism"]["macro_source"] == "plan"
        assert payload["stats"]["metabolism"]["daily_target"] == 2240
        assert payload["stats"]["calories"] == {
            "consumed": 0.0,
            "target": 2240.0,
            "percent": 0.0,
        }
        assert payload["stats"]["metabolism"]["macro_targets"] != {
            "protein": 155,
            "carbs": 205,
            "fat": 60,
        }
    finally:
        app.dependency_overrides.clear()
