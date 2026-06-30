from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from pydantic import BaseModel
from pydantic_ai.messages import ModelRequest, ModelResponse

from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender
from src.repositories.chat_repository import ChatRepository
from src.repositories.prompt_repository import PromptRepository
from src.repositories.token_repository import TokenRepository


class FakeUpdateResult:
    def __init__(self, *, upserted_id: ObjectId | None = None, modified_count: int = 0):
        self.upserted_id = upserted_id
        self.modified_count = modified_count


class FakeDeleteResult:
    def __init__(self, deleted_count: int) -> None:
        self.deleted_count = deleted_count


class FakeInsertManyResult:
    def __init__(self, inserted_ids: list[ObjectId]) -> None:
        self.inserted_ids = inserted_ids


class FakeInsertOneResult:
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
            if isinstance(value, dict):
                current = doc.get(key)
                if "$lt" in value and not (current < value["$lt"]):
                    return False
                if "$nin" in value and current in value["$nin"]:
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
                return FakeUpdateResult(modified_count=0 if doc == original else 1)

        if upsert:
            inserted_id = ObjectId()
            new_doc = {"_id": inserted_id, **deepcopy(update.get("$set", {}))}
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

    def insert_one(self, document: dict) -> FakeInsertOneResult:
        inserted_id = ObjectId()
        self.docs.append({"_id": inserted_id, **deepcopy(document)})
        return FakeInsertOneResult(inserted_id)

    def delete_many(self, query: dict) -> None:
        self.docs = [doc for doc in self.docs if not self._matches(doc, query)]

    def count_documents(self, query: dict) -> int:
        return len([doc for doc in self.docs if self._matches(doc, query)])


class FakeDatabase:
    def __init__(self) -> None:
        self._collections: dict[str, FakeCollection] = {}

    def __getitem__(self, name: str) -> FakeCollection:
        if name not in self._collections:
            self._collections[name] = FakeCollection()
        return self._collections[name]


def test_chat_repository_roundtrip_persists_public_history_and_filters_system_messages():
    repo = ChatRepository(FakeDatabase())
    session_id = "chat-session-1"
    repo.add_messages(
        [
            ChatHistory(
                text="Quero ajustar meu plano",
                sender=Sender.STUDENT,
                timestamp="2026-06-01T10:00:00",
            ),
            ChatHistory(
                text="✅ Tool plan_ops executada",
                sender=Sender.STUDENT,
                timestamp="2026-06-01T10:01:00",
            ),
            ChatHistory(
                text="Plano ajustado com sucesso",
                sender=Sender.TRAINER,
                timestamp="2026-06-01T10:02:00",
                trainer_type="atlas",
                translations={"pt-BR": "Plano ajustado com sucesso"},
            ),
        ],
        session_id,
        trainer_type="atlas",
    )

    history = repo.get_history(session_id, limit=10, offset=0)
    assert [message.text for message in history] == [
        "Quero ajustar meu plano",
        "Plano ajustado com sucesso",
    ]
    assert history[0].sender == Sender.STUDENT
    assert history[1].sender == Sender.TRAINER
    assert history[1].trainer_type == "atlas"

    window_memory = repo.get_window_memory(session_id, k=10)
    assert [message.text for message in window_memory.messages] == [
        "Quero ajustar meu plano",
        "Plano ajustado com sucesso",
    ]

    pydantic_history = repo.get_pydantic_ai_history(session_id, limit=10)
    assert isinstance(pydantic_history[0], ModelRequest)
    assert isinstance(pydantic_history[1], ModelResponse)


def test_prompt_repository_roundtrip_logs_trims_and_sanitizes_prompt_payload():
    repo = PromptRepository(FakeDatabase())

    class DummyModel(BaseModel):
        name: str
        val: int

    for index in range(4):
        repo.log_prompt(
            "prompt@test.com",
            {
                "model": DummyModel(name=f"m{index}", val=index),
                "tokens_input": 100 + index,
                "tokens_output": 20 + index,
                "duration_ms": 300 + index,
                "requested_model": "gpt-x",
                "resolved_model": "gpt-x-real",
                "status": "success",
            },
            max_logs=2,
        )

    prompts = repo.get_user_prompts("prompt@test.com", limit=10)
    assert len(prompts) == 2
    assert prompts[0]["prompt"]["model"] == {"name": "m3", "val": 3}
    assert prompts[1]["prompt"]["model"] == {"name": "m2", "val": 2}
    assert all(doc["user_email"] == "prompt@test.com" for doc in prompts)


def test_token_repository_roundtrip_adds_and_updates_blocklist_entries():
    repo = TokenRepository(FakeDatabase())
    first_expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    second_expiration = datetime.now(timezone.utc) + timedelta(hours=2)

    repo.add_to_blocklist("jwt-token", first_expiration)
    assert repo.is_blocklisted("jwt-token") is True

    repo.add_to_blocklist("jwt-token", second_expiration)
    stored = repo.collection.find_one({"token": "jwt-token"})
    assert stored is not None
    assert stored["expires_at"] == second_expiration
    assert repo.is_blocklisted("missing-token") is False
