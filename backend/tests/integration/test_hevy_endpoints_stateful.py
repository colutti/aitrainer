from __future__ import annotations

from copy import deepcopy
from datetime import datetime

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.user_profile import UserProfile
from src.core.deps import get_ai_trainer_brain, get_hevy_service, get_mongo_database
from src.repositories.user_repository import UserRepository
from src.services.auth import verify_token


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        return all(doc.get(key) == value for key, value in query.items())

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
        for doc in self.docs:
            if self._matches(doc, query):
                found = deepcopy(doc)
                if projection:
                    keep = {key for key, value in projection.items() if value}
                    if keep:
                        found = {
                            key: value
                            for key, value in found.items()
                            if key in keep or key == "_id"
                        }
                return found
        return None


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulHevyDb:
    def __init__(self) -> None:
        self.repo = UserRepository(FakeDatabase())

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.repo.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.repo.save_profile(profile)

    def is_demo_user(self, _email: str) -> bool:
        return False


class FakeHevyService:
    def __init__(self) -> None:
        self.last_import_args: dict | None = None

    async def validate_api_key(self, api_key: str) -> bool:
        return api_key == "hevy_valid_key_4321"

    async def get_workout_count(self, api_key: str) -> int:
        return 18 if api_key == "hevy_valid_key_4321" else 0

    async def import_workouts(
        self,
        *,
        user_email: str,
        api_key: str,
        from_date: datetime | None,
        mode: str,
    ) -> dict:
        self.last_import_args = {
            "user_email": user_email,
            "api_key": api_key,
            "from_date": from_date,
            "mode": mode,
        }
        return {"imported": 4, "skipped": 1, "updated": 0}


def _seed_profile(fake_db: StatefulHevyDb, email: str, plan: str = "Pro") -> None:
    fake_db.save_user_profile(
        UserProfile(
            email=email,
            role="user",
            gender="Masculino",
            age=29,
            weight=82.0,
            height=180,
            goal_type="maintain",
            weekly_rate=0.0,
            target_weight=None,
            subscription_plan=plan,
            onboarding_completed=True,
            hevy_enabled=False,
            hevy_api_key=None,
            hevy_last_sync=None,
        )
    )


def test_hevy_roundtrip_persists_config_import_status_and_clear_key():
    user_email = "hevy-pro@example.com"
    fake_db = StatefulHevyDb()
    fake_service = FakeHevyService()
    _seed_profile(fake_db, user_email, plan="Pro")

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: fake_db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: fake_db
    app.dependency_overrides[get_hevy_service] = lambda: fake_service

    try:
        validate_response = client.post(
            "/integrations/hevy/validate",
            json={"api_key": "hevy_valid_key_4321"},
        )
        assert validate_response.status_code == 200
        assert validate_response.json() == {"valid": True, "count": 18}

        save_response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "hevy_valid_key_4321", "enabled": True},
        )
        assert save_response.status_code == 200
        assert save_response.json()["enabled"] is True
        assert save_response.json()["hasKey"] is True
        assert save_response.json()["apiKeyMasked"] == "****4321"
        assert save_response.json()["lastSync"] is None

        persisted_after_save = fake_db.get_user_profile(user_email)
        assert persisted_after_save is not None
        assert persisted_after_save.hevy_enabled is True
        assert persisted_after_save.hevy_api_key == "hevy_valid_key_4321"

        status_after_save = client.get("/integrations/hevy/status")
        assert status_after_save.status_code == 200
        assert status_after_save.json()["apiKeyMasked"] == "****4321"
        assert status_after_save.json()["lastSync"] is None

        count_response = client.get("/integrations/hevy/count")
        assert count_response.status_code == 200
        assert count_response.json() == {"count": 18}

        import_response = client.post(
            "/integrations/hevy/import",
            json={"mode": "overwrite", "from_date": "2026-06-01T08:30:00"},
        )
        assert import_response.status_code == 200
        assert import_response.json() == {"imported": 4, "skipped": 1, "updated": 0}
        assert fake_service.last_import_args is not None
        assert fake_service.last_import_args["user_email"] == user_email
        assert fake_service.last_import_args["api_key"] == "hevy_valid_key_4321"
        assert fake_service.last_import_args["mode"] == "overwrite"
        assert fake_service.last_import_args["from_date"] == datetime.fromisoformat(
            "2026-06-01T08:30:00"
        )

        status_after_import = client.get("/integrations/hevy/status")
        assert status_after_import.status_code == 200
        status_payload = status_after_import.json()
        assert status_payload["enabled"] is True
        assert status_payload["hasKey"] is True
        assert status_payload["apiKeyMasked"] == "****4321"
        assert isinstance(status_payload["lastSync"], str)
        assert "T" in status_payload["lastSync"]

        clear_response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "", "enabled": False},
        )
        assert clear_response.status_code == 200
        clear_payload = clear_response.json()
        assert clear_payload["enabled"] is False
        assert clear_payload["hasKey"] is False
        assert clear_payload["apiKeyMasked"] is None
        assert clear_payload["lastSync"] == status_payload["lastSync"]

        persisted_after_clear = fake_db.get_user_profile(user_email)
        assert persisted_after_clear is not None
        assert persisted_after_clear.hevy_enabled is False
        assert persisted_after_clear.hevy_api_key is None
        assert persisted_after_clear.hevy_last_sync is not None
    finally:
        app.dependency_overrides.clear()


def test_hevy_config_and_status_reject_basic_plan_users():
    user_email = "hevy-basic@example.com"
    fake_db = StatefulHevyDb()
    _seed_profile(fake_db, user_email, plan="Basic")

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: fake_db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: fake_db
    app.dependency_overrides[get_hevy_service] = lambda: FakeHevyService()

    try:
        save_response = client.post(
            "/integrations/hevy/config",
            json={"api_key": "hevy_valid_key_4321", "enabled": True},
        )
        assert save_response.status_code == 403
        assert save_response.json()["detail"] == "INTEGRATION_NOT_ALLOWED_FOR_PLAN"

        status_response = client.get("/integrations/hevy/status")
        assert status_response.status_code == 403
        assert status_response.json()["detail"] == "INTEGRATION_NOT_ALLOWED_FOR_PLAN"
    finally:
        app.dependency_overrides.clear()
