from __future__ import annotations

from copy import deepcopy

from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from src.api.main import app
from src.api.models.user_profile import UserProfile
from src.core.deps import get_ai_trainer_brain, get_telegram_repository
from src.repositories.telegram_repository import TelegramRepository
from src.repositories.user_repository import UserRepository
from src.services.auth import verify_token


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


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
            if key == "$or":
                return any(self._matches(doc, branch) for branch in value)
            if isinstance(value, dict):
                current = doc.get(key)
                if "$gt" in value and current <= value["$gt"]:
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
        if "update_id" in data and any(
            doc.get("update_id") == data["update_id"] for doc in self.docs
        ):
            raise DuplicateKeyError("duplicate update_id")
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

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    def find_one_and_delete(self, query: dict) -> dict | None:
        for index, doc in enumerate(self.docs):
            if self._matches(doc, query):
                found = deepcopy(doc)
                del self.docs[index]
                return found
        return None


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulTelegramBrain:
    def __init__(self) -> None:
        database = FakeDatabase()
        self.users = UserRepository(database)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.users.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.users.save_profile(profile)


def _build_profile(email: str, subscription_plan: str) -> UserProfile:
    return UserProfile(
        email=email,
        role="user",
        gender="Masculino",
        age=30,
        weight=None,
        height=180,
        goal_type="maintain",
        weekly_rate=0.0,
        subscription_plan=subscription_plan,
        onboarding_completed=True,
        telegram_notify_on_workout=False,
        telegram_notify_on_nutrition=True,
        telegram_notify_on_weight=True,
    )


def test_telegram_endpoints_stateful_roundtrip_generate_link_status_and_unlink(monkeypatch):
    user_email = "telegram@test.com"
    repo = TelegramRepository(FakeDatabase())
    brain = StatefulTelegramBrain()
    brain.save_user_profile(_build_profile(user_email, "Pro"))

    monkeypatch.setattr(
        "src.api.endpoints.telegram.is_e2e_test_auth_enabled",
        lambda: True,
    )
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_telegram_repository] = lambda: repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        initial_status = client.get("/telegram/status")
        assert initial_status.status_code == 200
        assert initial_status.json() == {
            "linked": False,
            "telegram_username": None,
            "linked_at": None,
            "telegram_notify_on_workout": True,
            "telegram_notify_on_nutrition": False,
            "telegram_notify_on_weight": False,
        }

        code_response = client.post("/telegram/generate-code")
        assert code_response.status_code == 200
        code = code_response.json()["code"]
        assert len(code) == 6

        e2e_link_response = client.post(
            "/telegram/e2e-link",
            json={"chat_id": 987654321, "username": "e2e_telegram_user"},
        )
        assert e2e_link_response.status_code == 200
        assert e2e_link_response.json() == {"linked": True}

        linked_status = client.get("/telegram/status")
        assert linked_status.status_code == 200
        assert linked_status.json()["linked"] is True
        assert linked_status.json()["telegram_username"] == "e2e_telegram_user"
        assert linked_status.json()["telegram_notify_on_workout"] is False
        assert linked_status.json()["telegram_notify_on_nutrition"] is True
        assert linked_status.json()["telegram_notify_on_weight"] is True

        consumed_email = repo.validate_and_consume_code(code, 123123123, "bot_user")
        assert consumed_email == user_email
        relinked = repo.get_link_by_email(user_email)
        assert relinked is not None
        assert relinked.chat_id == 123123123
        assert relinked.telegram_username == "bot_user"

        unlink_response = client.post("/telegram/unlink")
        assert unlink_response.status_code == 200
        assert unlink_response.json()["message"] == "Unlinked successfully"

        final_status = client.get("/telegram/status")
        assert final_status.status_code == 200
        assert final_status.json()["linked"] is False
    finally:
        app.dependency_overrides.clear()


def test_telegram_endpoints_stateful_retries_on_code_collision(monkeypatch):
    user_email = "collision@test.com"
    repo = TelegramRepository(FakeDatabase())
    brain = StatefulTelegramBrain()
    brain.save_user_profile(_build_profile(user_email, "Pro"))

    code_chars = iter("AAAAAABBBBBB")
    original_insert_one = repo.codes_collection.insert_one
    insert_calls = {"count": 0}

    def flaky_insert_one(document: dict):
        insert_calls["count"] += 1
        if insert_calls["count"] == 1:
            raise DuplicateKeyError("duplicate telegram code")
        return original_insert_one(document)

    monkeypatch.setattr(
        "src.api.endpoints.telegram.is_e2e_test_auth_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        "src.repositories.telegram_repository.secrets.choice",
        lambda _alphabet: next(code_chars),
    )
    monkeypatch.setattr(repo.codes_collection, "insert_one", flaky_insert_one)
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_telegram_repository] = lambda: repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        code_response = client.post("/telegram/generate-code")
        assert code_response.status_code == 200
        assert code_response.json()["code"] == "BBBBBB"
        assert insert_calls["count"] == 2
        assert repo.codes_collection.find_one({"code": "AAAAAA"}) is None
        stored_code = repo.codes_collection.find_one({"code": "BBBBBB"})
        assert stored_code is not None
        assert stored_code["user_email"] == user_email
    finally:
        app.dependency_overrides.clear()


def test_telegram_endpoints_stateful_unlink_keeps_other_users_linked(monkeypatch):
    first_email = "owner-a@test.com"
    second_email = "owner-b@test.com"
    repo = TelegramRepository(FakeDatabase())
    brain = StatefulTelegramBrain()
    brain.save_user_profile(_build_profile(first_email, "Pro"))
    brain.save_user_profile(_build_profile(second_email, "Pro"))

    monkeypatch.setattr(
        "src.api.endpoints.telegram.is_e2e_test_auth_enabled",
        lambda: True,
    )
    app.dependency_overrides[get_telegram_repository] = lambda: repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        app.dependency_overrides[verify_token] = lambda: first_email
        first_link = client.post(
            "/telegram/e2e-link",
            json={"chat_id": 111111111, "username": "first_owner"},
        )
        assert first_link.status_code == 200

        app.dependency_overrides[verify_token] = lambda: second_email
        second_status = client.get("/telegram/status")
        assert second_status.status_code == 200
        assert second_status.json()["linked"] is False

        unlink_response = client.post("/telegram/unlink")
        assert unlink_response.status_code == 200
        assert unlink_response.json()["message"] == "Unlinked successfully"

        app.dependency_overrides[verify_token] = lambda: first_email
        first_status = client.get("/telegram/status")
        assert first_status.status_code == 200
        assert first_status.json()["linked"] is True
        assert first_status.json()["telegram_username"] == "first_owner"
    finally:
        app.dependency_overrides.clear()


def test_telegram_endpoints_stateful_forbid_basic_plan(monkeypatch):
    user_email = "basic@test.com"
    repo = TelegramRepository(FakeDatabase())
    brain = StatefulTelegramBrain()
    brain.save_user_profile(_build_profile(user_email, "Basic"))

    monkeypatch.setattr(
        "src.api.endpoints.telegram.is_e2e_test_auth_enabled",
        lambda: True,
    )
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_telegram_repository] = lambda: repo
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        generate_response = client.post("/telegram/generate-code")
        assert generate_response.status_code == 403
        assert generate_response.json()["detail"] == "TELEGRAM_NOT_ALLOWED_FOR_PLAN"

        status_response = client.get("/telegram/status")
        assert status_response.status_code == 403
        assert status_response.json()["detail"] == "TELEGRAM_NOT_ALLOWED_FOR_PLAN"
    finally:
        app.dependency_overrides.clear()
