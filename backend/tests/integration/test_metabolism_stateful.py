from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
from unittest.mock import patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.weight_repository import WeightRepository
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
                if "$gte" in value and current < value["$gte"]:
                    return False
                if "$lte" in value and current > value["$lte"]:
                    return False
                continue
            if current != value:
                return False
        return True

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

    def replace_one(self, query: dict, data: dict) -> FakeReplaceResult:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                self.docs[index] = {"_id": doc["_id"], **deepcopy(data)}
                return FakeReplaceResult(matched_count=1)
        return FakeReplaceResult(matched_count=0)

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


class StatefulMetabolismDb:
    def __init__(self) -> None:
        self.database = FakeDatabase()
        self.weight = WeightRepository(self.database)
        self.nutrition = NutritionRepository(self.database)

    def save_nutrition_log(self, log):
        return self.nutrition.save_log(log)

    def get_nutrition_by_id(self, log_id: str):
        return self.nutrition.get_log_by_id(log_id)

    def get_weight_logs_by_date_range(self, user_email: str, start_date: date, end_date: date):
        return self.weight.get_logs_by_date_range(user_email, start_date, end_date)

    def get_nutrition_logs_by_date_range(
        self,
        user_email: str,
        start_date: datetime,
        end_date: datetime,
    ):
        return self.nutrition.get_logs_by_date_range(user_email, start_date, end_date)

    def get_weight_logs(self, user_email: str, limit: int = 30):
        return self.weight.get_logs(user_email, limit)

    def get_nutrition_logs(self, user_email: str, limit: int = 30):
        return self.nutrition.get_logs(user_email, limit)

    def get_user_profile(self, _email: str):
        return None


class WeightBrain:
    def __init__(self, database: StatefulMetabolismDb) -> None:
        self.database = database


def test_metabolism_summary_roundtrips_persisted_weight_and_nutrition_without_plan_context():
    user_email = "metabolism@example.com"
    db = StatefulMetabolismDb()
    brain = WeightBrain(db)
    end_day = date(2026, 4, 8)
    start_day = end_day - timedelta(days=7)

    class FrozenDate(date):
        @classmethod
        def today(cls):
            return end_day

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        for offset in range(8):
            current_day = start_day + timedelta(days=offset)
            weight_response = client.post(
                "/weight",
                json={
                    "date": current_day.isoformat(),
                    "weight_kg": round(80.0 - (offset * 0.1), 1),
                    "body_fat_pct": 18.0,
                    "source": "manual",
                },
            )
            assert weight_response.status_code == 200

            nutrition_response = client.post(
                "/nutrition/log",
                json={
                    "date": f"{current_day.isoformat()}T12:00:00",
                    "source": "manual",
                    "calories": 2400 - (offset * 10),
                    "protein_grams": 180.0,
                    "carbs_grams": 240.0,
                    "fat_grams": 70.0,
                    "partial_logged": False,
                },
            )
            assert nutrition_response.status_code == 200

        with patch("src.services.adaptive_tdee.date", FrozenDate):
            response = client.get("/metabolism/summary?weeks=3")

        assert response.status_code == 200
        data = response.json()
        assert data["goal_type"] == "maintain"
        assert data["target_weight"] is None
        assert data["logs_count"] == 8
        assert data["nutrition_logs_count"] == 8
        assert data["weight_logs_count"] == 8
        assert data["startDate"] == "2026-04-01"
        assert data["endDate"] == "2026-04-08"
        assert data["latest_weight"] == 79.3
        assert len(data["weight_trend"]) == 8
        assert len(data["calorie_trend"]) == 8
        assert data["calorie_trend"][0] == {"date": "2026-04-01", "calories": 2400}
        assert data["calorie_trend"][-1] == {"date": "2026-04-08", "calories": 2330}
        assert isinstance(data["tdee"], int)
        assert data["daily_target"] <= data["tdee"]
    finally:
        app.dependency_overrides = {}
