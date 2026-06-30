from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from unittest.mock import patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_mongo_database
from src.repositories.workout_repository import WorkoutRepository
from src.services.auth import verify_token


client = TestClient(app)


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

    def sort(self, field: str, direction: int) -> FakeCursor:
        reverse = direction < 0
        self._docs.sort(key=lambda doc: doc.get(field), reverse=reverse)
        return self

    def skip(self, amount: int) -> FakeCursor:
        self._docs = self._docs[amount:]
        return self

    def limit(self, amount: int) -> FakeCursor:
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
            if doc.get(key) != value:
                return False
        return True

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
                doc = {key: value for key, value in doc.items() if key in keep or key == "_id"}
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

    def distinct(self, field: str, query: dict) -> list:
        values = []
        seen = set()

        for doc in self.docs:
            if not self._matches(doc, query):
                continue

            extracted: list = []
            if field == "workout_type":
                extracted = [doc.get("workout_type")]
            elif field == "exercises.name":
                extracted = [
                    exercise.get("name")
                    for exercise in doc.get("exercises", [])
                    if isinstance(exercise, dict)
                ]

            for value in extracted:
                if value not in seen:
                    seen.add(value)
                    values.append(value)

        return values


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulWorkoutDb:
    def __init__(self) -> None:
        self.workouts_repo = WorkoutRepository(FakeDatabase())

    def save_workout_log(self, workout):
        return self.workouts_repo.save_log(workout)

    def update_workout_log(self, workout_id: str, user_email: str, workout):
        return self.workouts_repo.update_log(workout_id, user_email, workout)

    def get_workout_by_id(self, workout_id: str):
        return self.workouts_repo.get_log_by_id(workout_id)

    def get_workouts_paginated(
        self,
        user_email: str,
        page: int = 1,
        page_size: int = 10,
        workout_type: str | None = None,
    ):
        return self.workouts_repo.get_paginated(user_email, page, page_size, workout_type)

    def delete_workout_log(self, workout_id: str) -> bool:
        return self.workouts_repo.delete_log(workout_id)

    def get_workout_stats(self, user_email: str):
        return self.workouts_repo.get_stats(user_email)

    def get_workout_types(self, user_email: str):
        return self.workouts_repo.get_types(user_email)

    def get_workout_exercise_names(self, user_email: str):
        return self.workouts_repo.get_exercise_names(user_email)


def test_workout_crud_roundtrips_all_supported_fields():
    user_email = "test@example.com"
    db = StatefulWorkoutDb()

    create_payload = {
        "date": "2026-03-17T10:00:00",
        "workout_type": "Hybrid Strength",
        "duration_minutes": 67,
        "source": "manual",
        "external_id": "hevy-workout-123",
        "exercises": [
            {
                "name": "Bench Press",
                "sets": 2,
                "reps_per_set": [10, 8],
                "weights_per_set": [60.0, 70.0],
                "distance_meters_per_set": [],
                "duration_seconds_per_set": [],
            },
            {
                "name": "Row Erg",
                "sets": 2,
                "reps_per_set": [1, 1],
                "weights_per_set": [],
                "distance_meters_per_set": [500.0, 500.0],
                "duration_seconds_per_set": [110, 115],
            },
        ],
    }
    update_payload = {
        "date": "2026-03-18T11:30:00",
        "workout_type": "Conditioning",
        "duration_minutes": 54,
        "source": "hevy",
        "external_id": "hevy-workout-456",
        "exercises": [
            {
                "name": "Deadlift",
                "sets": 3,
                "reps_per_set": [5, 5, 5],
                "weights_per_set": [100.0, 105.0, 110.0],
                "distance_meters_per_set": [],
                "duration_seconds_per_set": [],
            },
            {
                "name": "Assault Bike",
                "sets": 1,
                "reps_per_set": [1],
                "weights_per_set": [],
                "distance_meters_per_set": [1200.0],
                "duration_seconds_per_set": [180],
            },
        ],
    }

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        create_response = client.post("/workout", json=create_payload)
        assert create_response.status_code == 200
        created = create_response.json()
        workout_id = created["id"]
        assert created == {
            "id": workout_id,
            "user_email": user_email,
            "date": "2026-03-17T10:00:00",
            "workout_type": "Hybrid Strength",
            "duration_minutes": 67,
            "source": "manual",
            "external_id": "hevy-workout-123",
            "exercises": create_payload["exercises"],
        }

        update_response = client.put(f"/workout/{workout_id}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json() == {
            "id": workout_id,
            "user_email": user_email,
            "date": "2026-03-18T11:30:00",
            "workout_type": "Conditioning",
            "duration_minutes": 54,
            "source": "hevy",
            "external_id": "hevy-workout-456",
            "exercises": update_payload["exercises"],
        }

        list_response = client.get("/workout/list?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 1
        assert payload["workouts"][0]["id"] == workout_id
        assert payload["workouts"][0]["external_id"] == "hevy-workout-456"
        assert payload["workouts"][0]["exercises"][1]["distance_meters_per_set"] == [1200.0]
        assert payload["workouts"][0]["exercises"][1]["duration_seconds_per_set"] == [180]

        delete_response = client.delete(f"/workout/{workout_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Workout deleted successfully"

        after_delete = client.get("/workout/list?page=1&page_size=10")
        assert after_delete.status_code == 200
        assert after_delete.json()["total"] == 0
        assert after_delete.json()["workouts"] == []
    finally:
        app.dependency_overrides.clear()


def test_workout_stats_reflect_create_update_and_delete():
    user_email = "stats@example.com"
    db = StatefulWorkoutDb()
    now = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=9,
        minute=0,
        second=0,
        microsecond=0,
    )
    frozen_stats_now = week_start + timedelta(days=4)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is not None:
                return frozen_stats_now.astimezone(tz)
            return frozen_stats_now

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        create_one = client.post(
            "/workout",
            json={
                "date": week_start.isoformat(),
                "workout_type": "Push Day",
                "duration_minutes": 55,
                "source": "manual",
                "external_id": "push-001",
                "exercises": [
                    {
                        "name": "Bench Press",
                        "sets": 2,
                        "reps_per_set": [10, 8],
                        "weights_per_set": [60.0, 70.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    }
                ],
            },
        )
        assert create_one.status_code == 200
        workout_one_id = create_one.json()["id"]

        create_two = client.post(
            "/workout",
            json={
                "date": (week_start + timedelta(days=1)).isoformat(),
                "workout_type": "Pull Day",
                "duration_minutes": 60,
                "source": "manual",
                "external_id": "pull-001",
                "exercises": [
                    {
                        "name": "Deadlift",
                        "sets": 2,
                        "reps_per_set": [5, 5],
                        "weights_per_set": [100.0, 110.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    }
                ],
            },
        )
        assert create_two.status_code == 200
        workout_two_id = create_two.json()["id"]

        create_three = client.post(
            "/workout",
            json={
                "date": (week_start + timedelta(days=2)).isoformat(),
                "workout_type": "Leg Day",
                "duration_minutes": 70,
                "source": "manual",
                "external_id": "legs-001",
                "exercises": [
                    {
                        "name": "Squat",
                        "sets": 2,
                        "reps_per_set": [5, 5],
                        "weights_per_set": [120.0, 125.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    }
                ],
            },
        )
        assert create_three.status_code == 200
        workout_three_id = create_three.json()["id"]

        update_two = client.put(
            f"/workout/{workout_two_id}",
            json={
                "date": (week_start + timedelta(days=1)).isoformat(),
                "workout_type": "Pull Day Updated",
                "duration_minutes": 62,
                "source": "hevy",
                "external_id": "pull-002",
                "exercises": [
                    {
                        "name": "Deadlift",
                        "sets": 2,
                        "reps_per_set": [5, 5],
                        "weights_per_set": [105.0, 115.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    }
                ],
            },
        )
        assert update_two.status_code == 200

        with patch("src.repositories.workout_repository.datetime", FrozenDateTime):
            stats_response = client.get("/workout/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()

        push_volume = (10 * 60.0) + (8 * 70.0)
        pull_volume = (5 * 105.0) + (5 * 115.0)
        leg_volume = (5 * 120.0) + (5 * 125.0)
        total_current_week_volume = push_volume + pull_volume + leg_volume

        assert stats_payload["total_workouts"] == 3
        assert stats_payload["current_streak_weeks"] == 1
        assert stats_payload["last_workout"]["id"] == workout_three_id
        assert stats_payload["last_workout"]["workout_type"] == "Leg Day"
        assert stats_payload["last_workout"]["external_id"] == "legs-001"

        expected_frequency = [False] * 7
        expected_frequency[week_start.weekday()] = True
        expected_frequency[(week_start + timedelta(days=1)).weekday()] = True
        expected_frequency[(week_start + timedelta(days=2)).weekday()] = True
        assert stats_payload["weekly_frequency"] == expected_frequency

        expected_weekly_volume = [
            {"category": "Leg Day", "volume": round(leg_volume, 1)},
            {"category": "Push Day", "volume": round(push_volume, 1)},
            {"category": "Pull Day Updated", "volume": round(pull_volume, 1)},
        ]
        assert stats_payload["weekly_volume"] == expected_weekly_volume

        assert stats_payload["recent_prs"][0]["exercise_name"] == "Squat"
        assert stats_payload["recent_prs"][0]["weight"] == 125.0
        pr_map = {
            pr["exercise_name"]: pr
            for pr in stats_payload["recent_prs"]
        }
        assert pr_map["Bench Press"]["weight"] == 70.0
        assert pr_map["Deadlift"]["weight"] == 115.0
        assert pr_map["Deadlift"]["workout_id"] == workout_two_id

        assert stats_payload["volume_trend"][-1] == round(total_current_week_volume, 1)
        assert stats_payload["strength_radar"] == {
            "Push": 1.0,
            "Pull": 1.0,
            "Legs": 1.0,
        }

        delete_one = client.delete(f"/workout/{workout_one_id}")
        assert delete_one.status_code == 200
        assert delete_one.json()["message"] == "Workout deleted successfully"

        with patch("src.repositories.workout_repository.datetime", FrozenDateTime):
            stats_after_delete = client.get("/workout/stats")
        assert stats_after_delete.status_code == 200
        after_delete_payload = stats_after_delete.json()
        assert after_delete_payload["total_workouts"] == 2
        assert after_delete_payload["current_streak_weeks"] == 0
        assert after_delete_payload["weekly_frequency"] == [
            False if index == week_start.weekday() else expected_frequency[index]
            for index in range(7)
        ]
        assert after_delete_payload["volume_trend"][-1] == round(
            pull_volume + leg_volume,
            1,
        )
        assert {
            pr["exercise_name"] for pr in after_delete_payload["recent_prs"]
        } == {"Deadlift", "Squat"}
        assert after_delete_payload["strength_radar"] == {
            "Push": 0.0,
            "Pull": 1.0,
            "Legs": 1.0,
        }
    finally:
        app.dependency_overrides.clear()


def test_workout_types_and_exercises_reflect_create_update_and_delete():
    user_email = "catalog@example.com"
    db = StatefulWorkoutDb()

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        create_first = client.post(
            "/workout",
            json={
                "date": "2026-03-17T10:00:00",
                "workout_type": "Push Day",
                "duration_minutes": 45,
                "source": "manual",
                "exercises": [
                    {
                        "name": "Bench Press",
                        "sets": 2,
                        "reps_per_set": [10, 8],
                        "weights_per_set": [60.0, 70.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    },
                    {
                        "name": "Dips",
                        "sets": 1,
                        "reps_per_set": [12],
                        "weights_per_set": [0.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    },
                ],
            },
        )
        assert create_first.status_code == 200
        first_workout_id = create_first.json()["id"]

        create_second = client.post(
            "/workout",
            json={
                "date": "2026-03-18T10:00:00",
                "workout_type": "Leg Day",
                "duration_minutes": 55,
                "source": "manual",
                "exercises": [
                    {
                        "name": "Squat",
                        "sets": 2,
                        "reps_per_set": [5, 5],
                        "weights_per_set": [120.0, 125.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    }
                ],
            },
        )
        assert create_second.status_code == 200
        second_workout_id = create_second.json()["id"]

        types_after_create = client.get("/workout/types")
        exercises_after_create = client.get("/workout/exercises")
        assert types_after_create.status_code == 200
        assert exercises_after_create.status_code == 200
        assert types_after_create.json() == ["Leg Day", "Push Day"]
        assert exercises_after_create.json() == ["Bench Press", "Dips", "Squat"]

        update_first = client.put(
            f"/workout/{first_workout_id}",
            json={
                "date": "2026-03-19T10:00:00",
                "workout_type": "Pull Day",
                "duration_minutes": 50,
                "source": "manual",
                "exercises": [
                    {
                        "name": "Barbell Row",
                        "sets": 2,
                        "reps_per_set": [12, 10],
                        "weights_per_set": [40.0, 45.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    },
                    {
                        "name": "Deadlift",
                        "sets": 1,
                        "reps_per_set": [5],
                        "weights_per_set": [140.0],
                        "distance_meters_per_set": [],
                        "duration_seconds_per_set": [],
                    },
                ],
            },
        )
        assert update_first.status_code == 200

        types_after_update = client.get("/workout/types")
        exercises_after_update = client.get("/workout/exercises")
        assert types_after_update.json() == ["Leg Day", "Pull Day"]
        assert exercises_after_update.json() == ["Barbell Row", "Deadlift", "Squat"]

        delete_second = client.delete(f"/workout/{second_workout_id}")
        assert delete_second.status_code == 200

        types_after_delete = client.get("/workout/types")
        exercises_after_delete = client.get("/workout/exercises")
        assert types_after_delete.json() == ["Pull Day"]
        assert exercises_after_delete.json() == ["Barbell Row", "Deadlift"]
    finally:
        app.dependency_overrides.clear()
