from __future__ import annotations

from copy import deepcopy
from datetime import date
from io import BytesIO

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.weight_log import WeightLog
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.repositories.weight_repository import WeightRepository
from src.services.adaptive_tdee import AdaptiveTDEEService
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
            if isinstance(value, dict):
                current = doc.get(key)
                if "$gte" in value and current < value["$gte"]:
                    return False
                if "$lte" in value and current > value["$lte"]:
                    return False
                continue
            if doc.get(key) != value:
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
            new_doc = {"_id": inserted_id, **deepcopy(query), **deepcopy(update.get("$set", {}))}
            self.docs.append(new_doc)
            return FakeUpdateResult(upserted_id=inserted_id, modified_count=0)

        return FakeUpdateResult(modified_count=0)

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

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor([deepcopy(doc) for doc in self.docs if self._matches(doc, query)])

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


class StatefulWeightDb:
    def __init__(self) -> None:
        self.weight = WeightRepository(FakeDatabase())

    def save_weight_log(self, log: WeightLog):
        return self.weight.save_log(log)

    def get_weight_paginated(self, user_email: str, page: int = 1, page_size: int = 10):
        return self.weight.get_paginated(user_email, page, page_size)

    def delete_weight_log(self, user_email: str, log_date):
        return self.weight.delete_log(user_email, log_date)

    def get_weight_logs(self, user_email: str, limit: int = 30):
        return self.weight.get_logs(user_email, limit)


class WeightBrain:
    def __init__(self, database: StatefulWeightDb) -> None:
        self.database = database


def test_weight_crud_roundtrips_all_fields_and_trend_weight():
    user_email = "test@example.com"
    db = StatefulWeightDb()
    brain = WeightBrain(db)

    create_payload = {
        "date": "2026-03-17",
        "weight_kg": 80.2,
        "body_fat_pct": 18.4,
        "muscle_mass_pct": 40.8,
        "muscle_mass_kg": 32.8,
        "bone_mass_kg": 3.5,
        "body_water_pct": 57.9,
        "visceral_fat": 8,
        "bmr": 1788,
        "bmi": 25.1,
        "neck_cm": 39.0,
        "chest_cm": 104.0,
        "waist_cm": 84.0,
        "hips_cm": 98.5,
        "bicep_r_cm": 36.5,
        "bicep_l_cm": 36.0,
        "thigh_r_cm": 58.0,
        "thigh_l_cm": 57.5,
        "calf_r_cm": 38.0,
        "calf_l_cm": 37.5,
        "source": "manual",
        "notes": "initial weight note",
    }
    update_payload = {
        "date": "2026-03-18",
        "weight_kg": 79.8,
        "body_fat_pct": 17.1,
        "muscle_mass_pct": 41.4,
        "muscle_mass_kg": 33.1,
        "bone_mass_kg": 3.4,
        "body_water_pct": 58.2,
        "visceral_fat": 7,
        "bmr": 1760,
        "bmi": 24.9,
        "neck_cm": 39.5,
        "chest_cm": 104.5,
        "waist_cm": 83.0,
        "hips_cm": 98.0,
        "bicep_r_cm": 36.0,
        "bicep_l_cm": 35.5,
        "thigh_r_cm": 57.0,
        "thigh_l_cm": 56.5,
        "calf_r_cm": 37.5,
        "calf_l_cm": 37.0,
        "source": "manual",
        "notes": "updated weight note",
    }

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        # Seed previous log for trend continuity.
        db.weight.save_log(
            WeightLog(
                user_email=user_email,
                date=date(2026, 3, 16),
                weight_kg=80.0,
                trend_weight=79.4,
            )
        )

        expected_create_trend = round(
            AdaptiveTDEEService(db).calculate_ema_trend(80.2, 79.4), 2
        )
        expected_update_trend = round(
            AdaptiveTDEEService(db).calculate_ema_trend(79.8, expected_create_trend), 2
        )

        create_response = client.post("/weight", json=create_payload)
        assert create_response.status_code == 200
        created = create_response.json()
        assert created == {
            "message": "Weight logged successfully",
            "id": created["id"],
            "is_new": True,
            "date": "2026-03-17",
            "trend_weight": expected_create_trend,
        }

        update_response = client.put(f"/weight/{created['id']}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json() == {
            "message": "Weight log updated successfully",
            "id": created["id"],
            "date": "2026-03-18",
            "trend_weight": expected_update_trend,
        }

        list_response = client.get("/weight?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 2
        assert payload["logs"][0]["id"] == created["id"]
        assert payload["logs"][0]["body_fat_pct"] == 17.1
        assert payload["logs"][0]["muscle_mass_kg"] == 33.1
        assert payload["logs"][0]["waist_cm"] == 83.0
        assert payload["logs"][0]["notes"] == "updated weight note"
        assert round(payload["logs"][0]["trend_weight"], 2) == expected_update_trend

        delete_response = client.delete("/weight/2026-03-18")
        assert delete_response.status_code == 200
        assert delete_response.json() == {
            "message": "Weight log deleted successfully",
            "deleted": True,
        }

        after_delete = client.get("/weight?page=1&page_size=10")
        assert after_delete.status_code == 200
        assert after_delete.json()["total"] == 1
        assert after_delete.json()["logs"][0]["date"] == "2026-03-16"
        assert after_delete.json()["logs"][0]["trend_weight"] == 79.4
    finally:
        app.dependency_overrides.clear()


def test_weight_stats_reflect_updated_latest_values_and_keep_zero_fat_entries():
    user_email = "stats@example.com"
    db = StatefulWeightDb()
    brain = WeightBrain(db)

    create_payload = {
        "date": "2026-03-17",
        "weight_kg": 80.2,
        "body_fat_pct": 18.4,
        "muscle_mass_pct": 40.8,
        "muscle_mass_kg": 32.8,
        "bmr": 1788,
        "source": "manual",
        "notes": "initial weight note",
    }
    update_payload = {
        "date": "2026-03-18",
        "weight_kg": 79.8,
        "body_fat_pct": 0.0,
        "muscle_mass_pct": 0.0,
        "muscle_mass_kg": 0.0,
        "bmr": 1760,
        "source": "manual",
        "notes": "updated zero body fat note",
    }

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        db.weight.save_log(
            WeightLog(
                user_email=user_email,
                date=date(2026, 3, 16),
                weight_kg=80.0,
                trend_weight=79.4,
                body_fat_pct=19.1,
                muscle_mass_pct=39.0,
                muscle_mass_kg=31.2,
                bmr=1800,
            )
        )

        create_response = client.post("/weight", json=create_payload)
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        update_response = client.put(f"/weight/{created_id}", json=update_payload)
        assert update_response.status_code == 200

        stats_response = client.get("/weight/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()

        assert stats_payload["latest"]["date"] == "2026-03-18"
        assert stats_payload["latest"]["weight_kg"] == 79.8
        assert stats_payload["latest"]["body_fat_pct"] == 0.0
        assert stats_payload["latest"]["muscle_mass_pct"] == 0.0
        assert stats_payload["latest"]["muscle_mass_kg"] == 0.0
        assert stats_payload["latest"]["bmr"] == 1760
        assert stats_payload["latest"]["notes"] == "updated zero body fat note"

        assert stats_payload["weight_trend"] == [
            {"date": "2026-03-16", "value": 80.0},
            {"date": "2026-03-18", "value": 79.8},
        ]
        assert stats_payload["fat_trend"] == [
            {"date": "2026-03-16", "value": 19.1},
            {"date": "2026-03-18", "value": 0.0},
        ]
        assert stats_payload["muscle_trend"] == [
            {"date": "2026-03-16", "value": 31.2},
            {"date": "2026-03-18", "value": 0.0},
        ]

        delete_updated = client.delete("/weight/2026-03-18")
        assert delete_updated.status_code == 200
        delete_seed = client.delete("/weight/2026-03-16")
        assert delete_seed.status_code == 200

        empty_stats_response = client.get("/weight/stats")
        assert empty_stats_response.status_code == 200
        assert empty_stats_response.json() == {
            "latest": None,
            "weight_trend": [],
            "fat_trend": [],
            "muscle_trend": [],
        }
    finally:
        app.dependency_overrides.clear()


def test_weight_import_zepp_life_persists_upserts_and_updates_stats():
    user_email = "import@example.com"
    db = StatefulWeightDb()
    brain = WeightBrain(db)

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        db.weight.save_log(
            WeightLog(
                user_email=user_email,
                date=date(2026, 3, 17),
                weight_kg=81.0,
                body_fat_pct=21.0,
                source="manual",
                notes="before import",
                trend_weight=80.8,
            )
        )

        csv_content = (
            "time,weight,fatRate,muscleRate,boneMass,bodyWaterRate,visceralFat,metabolism,bmi\n"
            "2026-03-17 07:00:00,80.5,null,40.0,3.4,57.1,8,1780,25.0\n"
            "2026-03-17 08:00:00,80.4,20.2,40.1,3.5,57.3,8,1785,24.9\n"
            "2026-03-18 08:30:00,80.0,19.8,40.4,3.5,57.8,7,1770,24.7\n"
        )

        import_response = client.post(
            "/weight/import/zepp-life",
            files={"file": ("zepp.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )

        assert import_response.status_code == 200
        assert import_response.json() == {
            "created": 1,
            "updated": 1,
            "errors": 0,
            "total_days": 2,
            "error_messages": [],
        }

        list_response = client.get("/weight?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 2
        assert payload["logs"][0]["date"] == "2026-03-18"
        assert payload["logs"][0]["weight_kg"] == 80.0
        assert payload["logs"][0]["body_fat_pct"] == 19.8
        assert payload["logs"][0]["muscle_mass_pct"] == 40.4
        assert payload["logs"][0]["source"] == "zepp_life_import"
        assert payload["logs"][1]["date"] == "2026-03-17"
        assert payload["logs"][1]["weight_kg"] == 80.4
        assert payload["logs"][1]["body_fat_pct"] == 20.2
        assert payload["logs"][1]["source"] == "zepp_life_import"

        stats_response = client.get("/weight/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()
        assert stats_payload["latest"]["date"] == "2026-03-18"
        assert stats_payload["latest"]["weight_kg"] == 80.0
        assert stats_payload["latest"]["body_fat_pct"] == 19.8
        assert stats_payload["fat_trend"] == [
            {"date": "2026-03-17", "value": 20.2},
            {"date": "2026-03-18", "value": 19.8},
        ]
    finally:
        app.dependency_overrides.clear()


def test_weight_update_allows_clearing_optional_body_fields():
    user_email = "clear-weight@example.com"
    db = StatefulWeightDb()
    brain = WeightBrain(db)

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        create_response = client.post(
            "/weight",
            json={
                "date": "2026-03-17",
                "weight_kg": 82.1,
                "body_fat_pct": 20.0,
                "muscle_mass_pct": 39.5,
                "muscle_mass_kg": 32.4,
                "bone_mass_kg": 3.4,
                "body_water_pct": 56.8,
                "visceral_fat": 9,
                "bmr": 1810,
                "bmi": 25.4,
                "neck_cm": 40.0,
                "chest_cm": 106.0,
                "waist_cm": 86.0,
                "hips_cm": 99.0,
                "bicep_r_cm": 37.0,
                "bicep_l_cm": 36.5,
                "thigh_r_cm": 58.5,
                "thigh_l_cm": 58.0,
                "calf_r_cm": 38.5,
                "calf_l_cm": 38.0,
                "source": "manual",
                "notes": "all optional fields filled",
            },
        )
        assert create_response.status_code == 200
        log_id = create_response.json()["id"]

        update_response = client.put(
            f"/weight/{log_id}",
            json={
                "date": "2026-03-18",
                "weight_kg": 81.7,
                "body_fat_pct": None,
                "muscle_mass_pct": None,
                "muscle_mass_kg": None,
                "bone_mass_kg": None,
                "body_water_pct": None,
                "visceral_fat": None,
                "bmr": None,
                "bmi": None,
                "neck_cm": None,
                "chest_cm": None,
                "waist_cm": None,
                "hips_cm": None,
                "bicep_r_cm": None,
                "bicep_l_cm": None,
                "thigh_r_cm": None,
                "thigh_l_cm": None,
                "calf_r_cm": None,
                "calf_l_cm": None,
                "source": "manual",
                "notes": None,
            },
        )
        assert update_response.status_code == 200

        list_response = client.get("/weight?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 1
        log = payload["logs"][0]
        assert log["id"] == log_id
        assert log["date"] == "2026-03-18"
        assert log["body_fat_pct"] is None
        assert log["muscle_mass_pct"] is None
        assert log["muscle_mass_kg"] is None
        assert log["bone_mass_kg"] is None
        assert log["body_water_pct"] is None
        assert log["visceral_fat"] is None
        assert log["bmr"] is None
        assert log["bmi"] is None
        assert log["neck_cm"] is None
        assert log["chest_cm"] is None
        assert log["waist_cm"] is None
        assert log["hips_cm"] is None
        assert log["bicep_r_cm"] is None
        assert log["bicep_l_cm"] is None
        assert log["thigh_r_cm"] is None
        assert log["thigh_l_cm"] is None
        assert log["calf_r_cm"] is None
        assert log["calf_l_cm"] is None
        assert log["notes"] is None

        stats_response = client.get("/weight/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()
        assert stats_payload["latest"]["date"] == "2026-03-18"
        assert stats_payload["latest"]["body_fat_pct"] is None
        assert stats_payload["latest"]["muscle_mass_kg"] is None
        assert stats_payload["latest"]["notes"] is None
    finally:
        app.dependency_overrides.clear()
