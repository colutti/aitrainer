from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import datetime

from bson import ObjectId
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.api.models.user_profile import UserProfile
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.repositories.chat_repository import ChatRepository
from src.repositories.user_repository import UserRepository
from src.services.auth import verify_token


client = TestClient(app)


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeInsertManyResult:
    def __init__(self, inserted_ids: list[ObjectId]) -> None:
        self.inserted_ids = inserted_ids


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
            current = doc.get(key)
            if isinstance(value, dict):
                if "$lt" in value and not (current < value["$lt"]):
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

    def insert_many(self, documents: list[dict], ordered: bool = True) -> FakeInsertManyResult:
        inserted_ids: list[ObjectId] = []
        for document in documents:
            inserted_id = ObjectId()
            inserted_ids.append(inserted_id)
            self.docs.append({"_id": inserted_id, **deepcopy(document)})
        return FakeInsertManyResult(inserted_ids)


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


class StatefulMessageDb:
    def __init__(self) -> None:
        self.database = FakeDatabase()
        self.users = UserRepository(self.database)
        self.chat = ChatRepository(self.database)

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.users.get_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.users.save_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        return self.users.update_profile_fields(email, fields)

    def is_demo_user(self, email: str) -> bool:
        return self.users.is_demo_user(email)

    def get_chat_history(self, user_id: str, limit: int = 20, offset: int = 0):
        return self.chat.get_history(user_id, limit, offset)

    def add_many_to_history(
        self,
        chat_histories: list[ChatHistory],
        session_id: str,
        trainer_type: str | None = None,
    ) -> None:
        self.chat.add_messages(chat_histories, session_id, trainer_type)


class StatefulMessageBrain:
    def __init__(self, database: StatefulMessageDb) -> None:
        self.database = database

    def get_user_profile(self, email: str) -> UserProfile | None:
        return self.database.get_user_profile(email)

    def save_user_profile(self, profile: UserProfile) -> None:
        self.database.save_user_profile(profile)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        return self.database.update_user_profile_fields(email, fields)

    def get_or_create_user_profile(self, user_email: str) -> UserProfile:
        profile = self.get_user_profile(user_email)
        if profile:
            return profile
        profile = UserProfile(
            email=user_email,
            role="user",
            gender="Masculino",
            age=30,
            weight=80.0,
            height=175,
            goal="Melhorar condicionamento",
            goal_type="maintain",
            weekly_rate=0.0,
            subscription_plan="Free",
            onboarding_completed=True,
        )
        self.save_user_profile(profile)
        return profile

    def check_message_limits(self, _profile: UserProfile) -> bool:
        return False

    def get_chat_history(self, user_email: str, limit: int = 20, offset: int = 0):
        return self.database.get_chat_history(user_email, limit, offset)

    async def send_message_ai(
        self,
        user_email: str,
        user_input: str,
        background_tasks=None,
        message_options: dict | None = None,
    ):
        del background_tasks, message_options
        now = datetime.now().isoformat()
        self.database.add_many_to_history(
            [
                ChatHistory(
                    text=user_input,
                    sender=Sender.STUDENT,
                    timestamp=now,
                    trainer_type="atlas",
                ),
                ChatHistory(
                    text="✅ Tool plan_ops executada",
                    sender=Sender.SYSTEM,
                    timestamp=now,
                    trainer_type="atlas",
                ),
                ChatHistory(
                    text=f"Resposta para: {user_input}",
                    sender=Sender.TRAINER,
                    timestamp=now,
                    trainer_type="atlas",
                ),
            ],
            user_email,
            trainer_type="atlas",
        )
        yield f"Resposta para: {user_input}"


def _collect_stream_text(response) -> str:
    async def _collect() -> str:
        parts = []
        async for chunk in response.body_iterator:
            parts.append(chunk.decode() if isinstance(chunk, bytes) else chunk)
        return "".join(parts)

    return asyncio.run(_collect())


def test_message_endpoints_stateful_persist_public_history_and_timezone():
    user_email = "message@example.com"
    db = StatefulMessageDb()
    brain = StatefulMessageBrain(db)

    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        first_response = client.post(
            "/message",
            json={"user_message": "Quero revisar meu treino"},
            headers={"Authorization": "Bearer token", "X-User-Timezone": "Europe/Madrid"},
        )
        assert first_response.status_code == 200
        assert "Resposta para: Quero revisar meu treino" in first_response.text

        second_response = client.post(
            "/message",
            json={"user_message": "E minha dieta?"},
            headers={"Authorization": "Bearer token", "X-User-Timezone": "Europe/Madrid"},
        )
        assert second_response.status_code == 200
        assert "Resposta para: E minha dieta?" in second_response.text

        history_response = client.get(
            "/message/history?limit=10&offset=0",
            headers={"Authorization": "Bearer token"},
        )
        assert history_response.status_code == 200
        payload = history_response.json()

        assert [item["text"] for item in payload] == [
            "Quero revisar meu treino",
            "Resposta para: Quero revisar meu treino",
            "E minha dieta?",
            "Resposta para: E minha dieta?",
        ]
        assert [item["sender"] for item in payload] == [
            "Student",
            "Trainer",
            "Student",
            "Trainer",
        ]
        assert all(item["trainer_type"] == "atlas" for item in payload if item["sender"] == "Trainer")
        assert all("✅ Tool" not in item["text"] for item in payload)

        paginated_response = client.get(
            "/message/history?limit=2&offset=1",
            headers={"Authorization": "Bearer token"},
        )
        assert paginated_response.status_code == 200
        assert [item["text"] for item in paginated_response.json()] == [
            "Resposta para: Quero revisar meu treino",
            "E minha dieta?",
        ]

        persisted_profile = db.get_user_profile(user_email)
        assert persisted_profile is not None
        assert persisted_profile.timezone == "Europe/Madrid"
    finally:
        app.dependency_overrides.clear()


def test_message_endpoints_stateful_isolates_users_and_paginates_turns():
    current_user = {"email": "alpha@example.com"}
    db = StatefulMessageDb()
    brain = StatefulMessageBrain(db)

    app.dependency_overrides[verify_token] = lambda: current_user["email"]
    app.dependency_overrides[get_mongo_database] = lambda: db
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain

    try:
        for user_email, message_text in [
            ("alpha@example.com", "Alpha turno 1"),
            ("beta@example.com", "Beta turno 1"),
            ("alpha@example.com", "Alpha turno 2"),
            ("alpha@example.com", "Alpha turno 3"),
        ]:
            current_user["email"] = user_email
            response = client.post(
                "/message",
                json={"user_message": message_text},
                headers={"Authorization": "Bearer token"},
            )
            assert response.status_code == 200
            assert f"Resposta para: {message_text}" in response.text

        current_user["email"] = "alpha@example.com"
        alpha_history_response = client.get(
            "/message/history?limit=10&offset=0",
            headers={"Authorization": "Bearer token"},
        )
        assert alpha_history_response.status_code == 200
        alpha_history = alpha_history_response.json()
        assert [item["text"] for item in alpha_history] == [
            "Alpha turno 1",
            "Resposta para: Alpha turno 1",
            "Alpha turno 2",
            "Resposta para: Alpha turno 2",
            "Alpha turno 3",
            "Resposta para: Alpha turno 3",
        ]
        assert [item["sender"] for item in alpha_history] == [
            "Student",
            "Trainer",
            "Student",
            "Trainer",
            "Student",
            "Trainer",
        ]
        assert all(
            item["trainer_type"] == "atlas"
            for item in alpha_history
            if item["sender"] == "Trainer"
        )
        assert all("Beta turno" not in item["text"] for item in alpha_history)

        alpha_page_response = client.get(
            "/message/history?limit=2&offset=2",
            headers={"Authorization": "Bearer token"},
        )
        assert alpha_page_response.status_code == 200
        assert [item["text"] for item in alpha_page_response.json()] == [
            "Alpha turno 2",
            "Resposta para: Alpha turno 2",
        ]

        current_user["email"] = "beta@example.com"
        beta_history_response = client.get(
            "/message/history?limit=10&offset=0",
            headers={"Authorization": "Bearer token"},
        )
        assert beta_history_response.status_code == 200
        assert [item["text"] for item in beta_history_response.json()] == [
            "Beta turno 1",
            "Resposta para: Beta turno 1",
        ]
    finally:
        app.dependency_overrides.clear()
