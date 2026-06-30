from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient

from src.api.main import app
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.core.config import settings
from src.services.auth import verify_token
from src.services.memory_service import add_memory, get_memories_paginated
from src.utils.qdrant_utils import point_to_dict


client = TestClient(app)


class _FakeQdrantClient:
    def __init__(self) -> None:
        self.collections: dict[str, list[SimpleNamespace]] = {}

    def get_collection(self, collection_name: str):
        if collection_name not in self.collections:
            raise ValueError("collection missing")
        return {"name": collection_name}

    def create_collection(self, collection_name: str, vectors_config=None) -> None:
        del vectors_config
        self.collections.setdefault(collection_name, [])

    def upsert(self, collection_name: str, points: list) -> None:
        bucket = self.collections.setdefault(collection_name, [])
        for point in points:
            for index, existing in enumerate(bucket):
                if str(existing.id) == str(point.id):
                    bucket[index] = point
                    break
            else:
                bucket.append(point)

    def count(self, collection_name: str, count_filter) -> SimpleNamespace:
        user_id = count_filter.must[0].match.value
        points = [
            point
            for point in self.collections.get(collection_name, [])
            if (point.payload or {}).get("user_id") == user_id
        ]
        return SimpleNamespace(count=len(points))

    def scroll(
        self,
        collection_name: str,
        scroll_filter,
        limit: int,
        offset=None,
        with_payload: bool = True,
    ):
        del limit, offset, with_payload
        user_id = scroll_filter.must[0].match.value
        points = [
            point
            for point in self.collections.get(collection_name, [])
            if (point.payload or {}).get("user_id") == user_id
        ]
        return points, None

    def retrieve(self, collection_name: str, ids: list[str]):
        ids_set = {str(memory_id) for memory_id in ids}
        return [
            point
            for point in self.collections.get(collection_name, [])
            if str(point.id) in ids_set
        ]

    def delete(self, collection_name: str, points_selector: list[str]) -> None:
        ids_set = {str(memory_id) for memory_id in points_selector}
        self.collections[collection_name] = [
            point
            for point in self.collections.get(collection_name, [])
            if str(point.id) not in ids_set
        ]


class _MemoryDb:
    def get_user_profile(self, _email: str):
        return None


class _StatefulMemoryBrain:
    def __init__(self, qdrant_client: _FakeQdrantClient) -> None:
        self._qdrant_client = qdrant_client

    async def add_memory(self, text: str, user_email: str) -> str:
        return add_memory(
            user_id=user_email,
            memory_data={"text": text},
            qdrant_client=self._qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )

    async def get_memories_paginated(
        self, user_id: str, page: int, page_size: int
    ) -> tuple[list[dict], int]:
        return get_memories_paginated(
            user_id=user_id,
            page=page,
            page_size=page_size,
            qdrant_client=self._qdrant_client,
            collection_name=settings.QDRANT_COLLECTION_NAME,
        )

    def get_memory_by_id(self, memory_id: str) -> dict | None:
        points = self._qdrant_client.retrieve(
            settings.QDRANT_COLLECTION_NAME,
            ids=[memory_id],
        )
        return point_to_dict(points[0]) if points else None

    def delete_memory(self, memory_id: str, user_email: str) -> None:
        del user_email
        self._qdrant_client.delete(
            settings.QDRANT_COLLECTION_NAME,
            points_selector=[memory_id],
        )


def _memory_payload(text: str, created_at: datetime) -> dict:
    return {
        "memory": text,
        "created_at": created_at.isoformat(),
        "updated_at": created_at.isoformat(),
    }


def test_memory_endpoints_roundtrip_create_list_delete_with_ownership_and_pagination():
    user_one = "test.one@example.com"
    user_two = "test.two@example.com"
    qdrant_client = _FakeQdrantClient()
    brain = _StatefulMemoryBrain(qdrant_client)

    app.dependency_overrides[verify_token] = lambda: user_one
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain
    app.dependency_overrides[get_mongo_database] = lambda: _MemoryDb()

    try:
        from unittest.mock import patch

        base_time = datetime(2026, 6, 28, 10, 0, 0)
        created_times = [base_time + timedelta(minutes=offset) for offset in range(4)]
        memory_ids = ["mem-1", "mem-2", "mem-3", "mem-4"]

        with (
            patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
            patch("src.services.memory_service.uuid4", side_effect=memory_ids),
            patch("src.services.memory_service.datetime") as mock_datetime,
        ):
            mock_datetime.utcnow.side_effect = created_times

            create_first = client.post("/memory", json=_memory_payload("primeira", created_times[0]))
            create_second = client.post("/memory", json=_memory_payload("segunda", created_times[1]))
            create_third = client.post("/memory", json=_memory_payload("terceira", created_times[2]))

        assert create_first.status_code == 200
        assert create_second.status_code == 200
        assert create_third.status_code == 200
        assert [create_first.json()["id"], create_second.json()["id"], create_third.json()["id"]] == [
            "mem-1",
            "mem-2",
            "mem-3",
        ]

        first_page = client.get("/memory/list?page=1&page_size=2")
        assert first_page.status_code == 200
        first_payload = first_page.json()
        assert first_payload["total"] == 3
        assert first_payload["page"] == 1
        assert first_payload["page_size"] == 2
        assert first_payload["total_pages"] == 2
        assert [item["id"] for item in first_payload["memories"]] == ["mem-3", "mem-2"]

        second_page = client.get("/memory/list?page=2&page_size=2")
        assert second_page.status_code == 200
        assert [item["id"] for item in second_page.json()["memories"]] == ["mem-1"]

        app.dependency_overrides[verify_token] = lambda: user_two
        with (
            patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
            patch("src.services.memory_service.uuid4", return_value=memory_ids[3]),
            patch("src.services.memory_service.datetime") as mock_datetime,
        ):
            mock_datetime.utcnow.return_value = created_times[3]
            create_fourth = client.post("/memory", json=_memory_payload("quarta", created_times[3]))

        assert create_fourth.status_code == 200
        assert create_fourth.json()["id"] == "mem-4"

        user_two_page = client.get("/memory/list?page=1&page_size=10")
        assert user_two_page.status_code == 200
        user_two_payload = user_two_page.json()
        assert user_two_payload["total"] == 1
        assert [item["id"] for item in user_two_payload["memories"]] == ["mem-4"]

        unauthorized_delete = client.delete("/memory/mem-1")
        assert unauthorized_delete.status_code == 403
        assert unauthorized_delete.json() == {
            "detail": "Not authorized to delete this memory"
        }

        app.dependency_overrides[verify_token] = lambda: user_one
        delete_response = client.delete("/memory/mem-2")
        assert delete_response.status_code == 200
        assert delete_response.json() == {"message": "Memory deleted successfully"}

        after_delete = client.get("/memory/list?page=1&page_size=10")
        assert after_delete.status_code == 200
        payload_after_delete = after_delete.json()
        assert payload_after_delete["total"] == 2
        assert [item["id"] for item in payload_after_delete["memories"]] == ["mem-3", "mem-1"]
    finally:
        app.dependency_overrides.clear()


def test_memory_endpoints_normalize_user_ids_and_return_404_after_delete():
    canonical_user = "normalized@example.com"
    noisy_user = "  NORMALIZED@example.com "
    qdrant_client = _FakeQdrantClient()
    brain = _StatefulMemoryBrain(qdrant_client)

    app.dependency_overrides[verify_token] = lambda: noisy_user
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain
    app.dependency_overrides[get_mongo_database] = lambda: _MemoryDb()

    try:
        from unittest.mock import patch

        created_at = datetime(2026, 6, 29, 9, 30, 0)

        with (
            patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
            patch("src.services.memory_service.uuid4", return_value="mem-normalized"),
            patch("src.services.memory_service.datetime") as mock_datetime,
        ):
            mock_datetime.utcnow.return_value = created_at
            create_response = client.post(
                "/memory",
                json=_memory_payload("lembranca normalizada", created_at),
            )

        assert create_response.status_code == 200
        assert create_response.json()["id"] == "mem-normalized"

        app.dependency_overrides[verify_token] = lambda: canonical_user

        list_response = client.get("/memory/list?page=1&page_size=10")
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 1
        assert [item["id"] for item in list_response.json()["memories"]] == [
            "mem-normalized"
        ]

        delete_response = client.delete("/memory/mem-normalized")
        assert delete_response.status_code == 200
        assert delete_response.json() == {"message": "Memory deleted successfully"}

        missing_response = client.delete("/memory/mem-normalized")
        assert missing_response.status_code == 404
        assert missing_response.json() == {"detail": "Memory not found"}
    finally:
        app.dependency_overrides.clear()
