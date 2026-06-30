from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from io import BytesIO

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.nutrition_log import NutritionLog
from src.api.models.user_profile import UserProfile
from src.core.deps import get_mongo_database
from src.repositories.nutrition_repository import NutritionRepository
from src.repositories.user_repository import UserRepository
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
                return FakeUpdateResult(
                    modified_count=0 if doc == original else 1,
                )

        if upsert:
            inserted_id = ObjectId()
            new_doc = {"_id": inserted_id, **deepcopy(query), **deepcopy(update.get("$set", {}))}
            self.docs.append(new_doc)
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


class StatefulNutritionDb:
    def __init__(self) -> None:
        database = FakeDatabase()
        self.nutrition = NutritionRepository(database)
        self.users = UserRepository(database)

    def save_nutrition_log(self, log):
        return self.nutrition.save_log(log)

    def update_nutrition_log(self, log_id: str, user_email: str, log):
        return self.nutrition.update_log(log_id, user_email, log)

    def get_nutrition_by_id(self, log_id: str):
        return self.nutrition.get_log_by_id(log_id)

    def get_nutrition_paginated(self, user_email: str, page: int = 1, page_size: int = 10, days=None):
        return self.nutrition.get_paginated(user_email, page, page_size, days)

    def delete_nutrition_log(self, log_id: str) -> bool:
        return self.nutrition.delete_log(log_id)

    def get_nutrition_stats(self, user_email: str):
        return self.nutrition.get_stats(user_email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.users.save_profile(profile)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.users.get_profile(email)


def test_nutrition_crud_roundtrips_all_supported_fields():
    user_email = "test@example.com"
    db = StatefulNutritionDb()

    create_payload = {
        "date": "2026-03-17T10:00:00",
        "source": "manual",
        "calories": 2500,
        "protein_grams": 150.0,
        "carbs_grams": 300.0,
        "fat_grams": 70.0,
        "fiber_grams": 30.0,
        "sugar_grams": 40.0,
        "sodium_mg": 1800.0,
        "cholesterol_mg": 220.0,
        "notes": "initial nutrition note",
        "partial_logged": True,
    }
    update_payload = {
        "date": "2026-03-18T12:30:00",
        "source": "myfitnesspal",
        "calories": 2350,
        "protein_grams": 165.0,
        "carbs_grams": 245.0,
        "fat_grams": 62.0,
        "fiber_grams": 34.0,
        "sugar_grams": 28.0,
        "sodium_mg": 1500.0,
        "cholesterol_mg": 180.0,
        "notes": "updated nutrition note",
        "partial_logged": False,
    }

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        create_response = client.post("/nutrition/log", json=create_payload)
        assert create_response.status_code == 200
        created = create_response.json()
        log_id = created["id"]
        assert created == {
            "id": log_id,
            "user_email": user_email,
            "date": "2026-03-17T00:00:00",
            "source": "manual",
            "calories": 2500,
            "protein_grams": 150.0,
            "carbs_grams": 300.0,
            "fat_grams": 70.0,
            "fiber_grams": 30.0,
            "sugar_grams": 40.0,
            "sodium_mg": 1800.0,
            "cholesterol_mg": 220.0,
            "notes": "initial nutrition note",
            "partial_logged": True,
        }

        update_response = client.put(f"/nutrition/log/{log_id}", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json() == {
            "id": log_id,
            "user_email": user_email,
            "date": "2026-03-18T00:00:00",
            "source": "myfitnesspal",
            "calories": 2350,
            "protein_grams": 165.0,
            "carbs_grams": 245.0,
            "fat_grams": 62.0,
            "fiber_grams": 34.0,
            "sugar_grams": 28.0,
            "sodium_mg": 1500.0,
            "cholesterol_mg": 180.0,
            "notes": "updated nutrition note",
            "partial_logged": False,
        }

        list_response = client.get("/nutrition/list?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 1
        assert payload["logs"][0]["id"] == log_id
        assert payload["logs"][0]["fiber_grams"] == 34.0
        assert payload["logs"][0]["sugar_grams"] == 28.0
        assert payload["logs"][0]["sodium_mg"] == 1500.0
        assert payload["logs"][0]["cholesterol_mg"] == 180.0
        assert payload["logs"][0]["notes"] == "updated nutrition note"
        assert payload["logs"][0]["partial_logged"] is False

        delete_response = client.delete(f"/nutrition/{log_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Nutrition log deleted successfully"

        after_delete = client.get("/nutrition/list?page=1&page_size=10")
        assert after_delete.status_code == 200
        assert after_delete.json()["total"] == 0
        assert after_delete.json()["logs"] == []
    finally:
        app.dependency_overrides.clear()


def test_nutrition_stats_and_today_reflect_created_and_updated_logs():
    user_email = "stats@example.com"
    db = StatefulNutritionDb()
    now = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        today_create = client.post(
            "/nutrition/log",
            json={
                "date": now.isoformat(),
                "source": "manual",
                "calories": 2100,
                "protein_grams": 140.0,
                "carbs_grams": 220.0,
                "fat_grams": 60.0,
                "fiber_grams": 25.0,
                "sugar_grams": 18.0,
                "sodium_mg": 1300.0,
                "cholesterol_mg": 170.0,
                "notes": "today initial",
                "partial_logged": True,
            },
        )
        assert today_create.status_code == 200
        today_id = today_create.json()["id"]

        today_update = client.put(
            f"/nutrition/log/{today_id}",
            json={
                "date": now.isoformat(),
                "source": "manual",
                "calories": 2250,
                "protein_grams": 155.0,
                "carbs_grams": 235.0,
                "fat_grams": 58.0,
                "fiber_grams": 28.0,
                "sugar_grams": 22.0,
                "sodium_mg": 1250.0,
                "cholesterol_mg": 160.0,
                "notes": "today updated",
                "partial_logged": False,
            },
        )
        assert today_update.status_code == 200

        yesterday_create = client.post(
            "/nutrition/log",
            json={
                "date": (now - timedelta(days=1)).isoformat(),
                "source": "manual",
                "calories": 1800,
                "protein_grams": 120.0,
                "carbs_grams": 180.0,
                "fat_grams": 55.0,
                "fiber_grams": 20.0,
                "notes": "yesterday",
                "partial_logged": False,
            },
        )
        assert yesterday_create.status_code == 200

        six_days_ago_create = client.post(
            "/nutrition/log",
            json={
                "date": (now - timedelta(days=6)).isoformat(),
                "source": "manual",
                "calories": 2000,
                "protein_grams": 130.0,
                "carbs_grams": 210.0,
                "fat_grams": 57.0,
                "fiber_grams": 22.0,
                "notes": "six days ago",
                "partial_logged": False,
            },
        )
        assert six_days_ago_create.status_code == 200

        thirteen_days_ago_create = client.post(
            "/nutrition/log",
            json={
                "date": (now - timedelta(days=13)).isoformat(),
                "source": "manual",
                "calories": 2500,
                "protein_grams": 170.0,
                "carbs_grams": 260.0,
                "fat_grams": 72.0,
                "fiber_grams": 30.0,
                "notes": "thirteen days ago",
                "partial_logged": False,
            },
        )
        assert thirteen_days_ago_create.status_code == 200

        stats_response = client.get("/nutrition/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()

        expected_avg_daily_calories = round((2250 + 1800 + 2000) / 3, 1)
        expected_avg_protein = round((155.0 + 120.0 + 130.0) / 3, 1)
        expected_avg_daily_calories_14_days = round(
            (2250 + 1800 + 2000 + 2500) / 4, 1
        )

        assert stats_payload["total_logs"] == 4
        assert stats_payload["avg_daily_calories"] == expected_avg_daily_calories
        assert stats_payload["avg_protein"] == expected_avg_protein
        assert (
            stats_payload["avg_daily_calories_14_days"]
            == expected_avg_daily_calories_14_days
        )
        assert len(stats_payload["last_7_days"]) == 7
        assert len(stats_payload["last_14_days"]) == 14
        assert stats_payload["today"]["id"] == today_id
        assert stats_payload["today"]["calories"] == 2250
        assert stats_payload["today"]["protein_grams"] == 155.0
        assert stats_payload["today"]["notes"] == "today updated"
        assert stats_payload["today"]["partial_logged"] is False

        current_week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        expected_adherence = [False] * 7
        for log_date in (
            now.replace(hour=0, minute=0, second=0, microsecond=0),
            (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0),
        ):
            if log_date >= current_week_start:
                expected_adherence[log_date.weekday()] = True
        assert stats_payload["weekly_adherence"] == expected_adherence

        today_response = client.get("/nutrition/today")
        assert today_response.status_code == 200
        assert today_response.json()["id"] == today_id
        assert today_response.json()["calories"] == 2250
        assert today_response.json()["notes"] == "today updated"
    finally:
        app.dependency_overrides.clear()


def test_nutrition_import_myfitnesspal_persists_daily_aggregation_upserts_and_stats():
    user_email = "import@example.com"
    db = StatefulNutritionDb()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)

    db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=30,
            weight=None,
            height=180,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Pro",
            onboarding_completed=True,
        )
    )

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        db.save_nutrition_log(
            NutritionLog(
                user_email=user_email,
                date=yesterday.replace(hour=8),
                source="manual",
                calories=2100,
                protein_grams=140.0,
                carbs_grams=220.0,
                fat_grams=65.0,
                notes="before import",
                partial_logged=False,
            )
        )

        csv_content = (
            "Data,Refeição,Calorias,Gorduras (g),Colesterol,S Sodium (mg),Carboidratos (g),Fibra,Açucar,Proteínas (g)\n"
            f"{yesterday.date().isoformat()},Cafe da manha,500,15,50,300,60,8,12,30\n"
            f"{yesterday.date().isoformat()},Almoco,700,20,70,500,80,10,18,40\n"
            f"{today.date().isoformat()},Jantar,900,25,90,650,100,12,20,55\n"
        )

        import_response = client.post(
            "/nutrition/import/myfitnesspal",
            files={"file": ("mfp.csv", BytesIO(csv_content.encode("utf-8")), "text/csv")},
        )

        assert import_response.status_code == 200
        assert import_response.json() == {
            "created": 1,
            "updated": 1,
            "errors": 0,
            "total_days": 2,
            "error_messages": [],
        }

        list_response = client.get("/nutrition/list?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 2
        assert payload["logs"][0]["date"] == today.isoformat()
        assert payload["logs"][0]["calories"] == 900
        assert payload["logs"][0]["protein_grams"] == 55.0
        assert payload["logs"][0]["fiber_grams"] == 12.0
        assert payload["logs"][0]["source"] == "myfitnesspal"
        assert payload["logs"][0]["notes"] == "Importado do MyFitnessPal (1 refeições)"
        assert payload["logs"][1]["date"] == yesterday.isoformat()
        assert payload["logs"][1]["calories"] == 1200
        assert payload["logs"][1]["protein_grams"] == 70.0
        assert payload["logs"][1]["carbs_grams"] == 140.0
        assert payload["logs"][1]["fat_grams"] == 35.0
        assert payload["logs"][1]["fiber_grams"] == 18.0
        assert payload["logs"][1]["sugar_grams"] == 30.0
        assert payload["logs"][1]["sodium_mg"] == 800.0
        assert payload["logs"][1]["cholesterol_mg"] == 120.0
        assert payload["logs"][1]["source"] == "myfitnesspal"
        assert payload["logs"][1]["notes"] == "Importado do MyFitnessPal (2 refeições)"

        today_response = client.get("/nutrition/today")
        assert today_response.status_code == 200

        stats_response = client.get("/nutrition/stats")
        assert stats_response.status_code == 200
        stats_payload = stats_response.json()
        assert stats_payload["total_logs"] == 2
        assert stats_payload["today"]["date"] == today.isoformat()
        assert stats_payload["today"]["calories"] == 900
    finally:
        app.dependency_overrides.clear()


def test_nutrition_update_allows_clearing_optional_fields():
    user_email = "clear-optional@example.com"
    db = StatefulNutritionDb()

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db

    try:
        create_response = client.post(
            "/nutrition/log",
            json={
                "date": "2026-03-17T10:00:00",
                "source": "manual",
                "calories": 2400,
                "protein_grams": 160.0,
                "carbs_grams": 250.0,
                "fat_grams": 68.0,
                "fiber_grams": 32.0,
                "sugar_grams": 26.0,
                "sodium_mg": 1400.0,
                "cholesterol_mg": 190.0,
                "notes": "filled optional fields",
                "partial_logged": True,
            },
        )
        assert create_response.status_code == 200
        log_id = create_response.json()["id"]

        update_response = client.put(
            f"/nutrition/log/{log_id}",
            json={
                "date": "2026-03-18T10:00:00",
                "source": "manual",
                "calories": 2200,
                "protein_grams": 150.0,
                "carbs_grams": 210.0,
                "fat_grams": 60.0,
                "fiber_grams": None,
                "sugar_grams": None,
                "sodium_mg": None,
                "cholesterol_mg": None,
                "notes": None,
                "partial_logged": False,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["fiber_grams"] is None
        assert update_response.json()["sugar_grams"] is None
        assert update_response.json()["sodium_mg"] is None
        assert update_response.json()["cholesterol_mg"] is None
        assert update_response.json()["notes"] is None
        assert update_response.json()["partial_logged"] is False

        list_response = client.get("/nutrition/list?page=1&page_size=10")
        assert list_response.status_code == 200
        payload = list_response.json()
        assert payload["total"] == 1
        assert payload["logs"][0]["id"] == log_id
        assert payload["logs"][0]["fiber_grams"] is None
        assert payload["logs"][0]["sugar_grams"] is None
        assert payload["logs"][0]["sodium_mg"] is None
        assert payload["logs"][0]["cholesterol_mg"] is None
        assert payload["logs"][0]["notes"] is None
        assert payload["logs"][0]["partial_logged"] is False
    finally:
        app.dependency_overrides.clear()
