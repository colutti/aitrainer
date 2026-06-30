from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.invite import Invite
from src.api.models.user_profile import UserProfile
from src.repositories.invite_repository import InviteRepository
from src.repositories.trainer_repository import TrainerRepository
from src.repositories.user_repository import UserRepository
from src.repositories.weight_repository import WeightRepository
from src.services.auth import verify_token


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeCursor:
    def __init__(self, docs: list[dict]) -> None:
        self._docs = docs

    def sort(self, field: str, direction: int) -> "FakeCursor":
        reverse = direction < 0
        self._docs.sort(key=lambda doc: doc.get(field), reverse=reverse)
        return self

    def limit(self, amount: int) -> "FakeCursor":
        self._docs = self._docs[:amount]
        return self

    def __iter__(self):
        return iter([deepcopy(doc) for doc in self._docs])


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict] = []

    def create_index(self, *_args, **_kwargs) -> None:
        return None

    def _matches(self, doc: dict, query: dict) -> bool:
        for key, value in query.items():
            if isinstance(value, dict):
                current = doc.get(key)
                if "$gt" in value and current <= value["$gt"]:
                    return False
                if "$gte" in value and current < value["$gte"]:
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
                for key, value in update.get("$inc", {}).items():
                    doc[key] = doc.get(key, 0) + value
                for key in update.get("$unset", {}):
                    doc.pop(key, None)
                return FakeUpdateResult(modified_count=0 if doc == original else 1)

        if upsert:
            inserted_id = ObjectId()
            new_doc = {"_id": inserted_id, **deepcopy(query), **deepcopy(update.get("$set", {}))}
            self.docs.append(new_doc)
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
                doc = {key: value for key, value in doc.items() if key in keep or key == "_id"}
        return doc

    def find(self, query: dict) -> FakeCursor:
        return FakeCursor([deepcopy(doc) for doc in self.docs if self._matches(doc, query)])

    def insert_one(self, data: dict):
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(data)})

        class _Result:
            def __init__(self, value: ObjectId) -> None:
                self.inserted_id = value

        return _Result(inserted_id)

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


class StatefulOnboardingDb:
    def __init__(self) -> None:
        database = FakeDatabase()
        self.invites = InviteRepository(database)
        self.users = UserRepository(database)
        self.trainers = TrainerRepository(database)
        self.weight = WeightRepository(database)

    def get_user_profile(self, email: str):
        return self.users.get_profile(email)

    def save_user_profile(self, profile):
        return self.users.save_profile(profile)

    def save_trainer_profile(self, trainer_profile):
        return self.trainers.save_profile(trainer_profile)

    def get_trainer_profile(self, email: str):
        return self.trainers.get_profile(email)


def test_complete_onboarding_stateful_creates_user_trainer_weight_and_marks_invite_used():
    db = StatefulOnboardingDb()
    invite = Invite(
        token="invite-token-123",
        email="newuser@test.com",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        used=False,
    )
    db.invites.create(invite)

    with (
        patch("src.api.endpoints.onboarding.get_mongo_database", return_value=db),
        patch("src.api.endpoints.onboarding.create_token", return_value="fake-jwt-token"),
    ):
        validate_response = client.get("/onboarding/validate?token=invite-token-123")
        assert validate_response.status_code == 200
        assert validate_response.json() == {
            "valid": True,
            "email": "newuser@test.com",
            "reason": None,
        }

        complete_response = client.post(
            "/onboarding/complete",
            json={
                "token": "invite-token-123",
                "password": "SecurePass1",
                "gender": "Masculino",
                "age": 32,
                "weight": 82.5,
                "height": 182,
                "trainer_type": "gymbro",
                "subscription_plan": "Pro",
            },
        )

        assert complete_response.status_code == 200
        assert complete_response.json() == {
            "token": "fake-jwt-token",
            "message": "Conta criada com sucesso!",
        }

        saved_profile = db.get_user_profile("newuser@test.com")
        assert saved_profile is not None
        assert saved_profile.subscription_plan == "Pro"
        assert saved_profile.gender == "Masculino"
        assert saved_profile.age == 32
        assert saved_profile.height == 182
        assert saved_profile.weight is None

        saved_trainer = db.get_trainer_profile("newuser@test.com")
        assert saved_trainer is not None
        assert saved_trainer.trainer_type == "gymbro"

        weight_logs = db.weight.get_logs("newuser@test.com", limit=10)
        assert len(weight_logs) == 1
        assert weight_logs[0].weight_kg == 82.5
        assert weight_logs[0].trend_weight == 82.5

        persisted_invite = db.invites.get_by_token("invite-token-123")
        assert persisted_invite is not None
        assert persisted_invite.used is True
        assert persisted_invite.used_at is not None

        reused_response = client.post(
            "/onboarding/complete",
            json={
                "token": "invite-token-123",
                "password": "SecurePass1",
                "gender": "Masculino",
                "age": 32,
                "weight": 82.5,
                "height": 182,
                "trainer_type": "gymbro",
                "subscription_plan": "Pro",
            },
        )
        assert reused_response.status_code == 409
        assert reused_response.json()["detail"] == "Invite already used"


def test_public_onboarding_stateful_updates_existing_user_and_overwrites_same_day_weight():
    user_email = "public@test.com"
    db = StatefulOnboardingDb()
    db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Male",
            age=25,
            weight=None,
            height=170,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Free",
            onboarding_completed=False,
        )
    )
    app.dependency_overrides[verify_token] = lambda: user_email

    with (
        patch("src.api.endpoints.onboarding.get_mongo_database", return_value=db),
        patch("src.api.endpoints.onboarding.create_token", return_value="new-jwt-token"),
        patch("src.api.endpoints.onboarding.are_new_user_signups_enabled", return_value=True),
    ):
        first_response = client.post(
            "/onboarding/profile",
            json={
                "gender": "Feminino",
                "age": 26,
                "weight": 65.0,
                "height": 168,
                "trainer_type": "atlas",
                "subscription_plan": "Free",
                "name": "Public User",
            },
        )
        assert first_response.status_code == 200
        assert first_response.json() == {
            "token": "new-jwt-token",
            "message": "Perfil configurado com sucesso!",
        }

        second_response = client.post(
            "/onboarding/profile",
            json={
                "gender": "Feminino",
                "age": 27,
                "weight": 66.2,
                "height": 169,
                "trainer_type": "sofia",
                "subscription_plan": "Pro",
                "name": "Updated User",
            },
        )
        assert second_response.status_code == 200

        saved_profile = db.get_user_profile(user_email)
        assert saved_profile is not None
        assert saved_profile.onboarding_completed is True
        assert saved_profile.display_name == "Updated User"
        assert saved_profile.age == 27
        assert saved_profile.height == 169
        assert saved_profile.subscription_plan == "Pro"

        saved_trainer = db.get_trainer_profile(user_email)
        assert saved_trainer is not None
        assert saved_trainer.trainer_type == "sofia"

        weight_logs = db.weight.get_logs(user_email, limit=10)
        assert len(weight_logs) == 1
        assert weight_logs[0].weight_kg == 66.2
        assert weight_logs[0].trend_weight == 66.2

    app.dependency_overrides.clear()


def test_public_onboarding_without_name_preserves_existing_display_name():
    user_email = "keep-name@test.com"
    db = StatefulOnboardingDb()
    db.save_user_profile(
        UserProfile(
            email=user_email,
            role="user",
            gender="Male",
            age=28,
            weight=None,
            height=175,
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Free",
            display_name="Existing Name",
            onboarding_completed=False,
        )
    )
    app.dependency_overrides[verify_token] = lambda: user_email

    with (
        patch("src.api.endpoints.onboarding.get_mongo_database", return_value=db),
        patch("src.api.endpoints.onboarding.create_token", return_value="preserved-name-token"),
        patch("src.api.endpoints.onboarding.are_new_user_signups_enabled", return_value=True),
    ):
        response = client.post(
            "/onboarding/profile",
            json={
                "gender": "Feminino",
                "age": 29,
                "weight": 64.3,
                "height": 166,
                "trainer_type": "atlas",
                "subscription_plan": "Basic",
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "token": "preserved-name-token",
            "message": "Perfil configurado com sucesso!",
        }

        saved_profile = db.get_user_profile(user_email)
        assert saved_profile is not None
        assert saved_profile.display_name == "Existing Name"
        assert saved_profile.gender == "Feminino"
        assert saved_profile.age == 29
        assert saved_profile.height == 166
        assert saved_profile.subscription_plan == "Basic"
        assert saved_profile.onboarding_completed is True

        saved_trainer = db.get_trainer_profile(user_email)
        assert saved_trainer is not None
        assert saved_trainer.trainer_type == "atlas"

        weight_logs = db.weight.get_logs(user_email, limit=10)
        assert len(weight_logs) == 1
        assert weight_logs[0].weight_kg == 64.3
        assert weight_logs[0].trend_weight == 64.3

    app.dependency_overrides.clear()
