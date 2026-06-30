from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.services.memory_service import add_memory, get_memories_paginated
from src.services.memory_tools import (
    create_delete_memory_tool,
    create_search_memory_tool,
    create_update_memory_tool,
)


class FakeQdrantClient:
    def __init__(self) -> None:
        self.collections: dict[str, list[SimpleNamespace]] = {}

    def get_collection(self, collection_name: str):
        if collection_name not in self.collections:
            raise ValueError("not found")
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
        del offset, with_payload
        user_id = scroll_filter.must[0].match.value
        points = [
            point
            for point in self.collections.get(collection_name, [])
            if (point.payload or {}).get("user_id") == user_id
        ]
        return points[:limit], None

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

    def query_points(
        self,
        collection_name: str,
        query,
        query_filter=None,
        limit: int = 5,
        score_threshold=None,
        with_payload: bool = True,
    ) -> SimpleNamespace:
        del query, score_threshold, with_payload
        points = self.collections.get(collection_name, [])
        if query_filter is not None:
            user_id = query_filter.must[0].match.value
            points = [
                point for point in points if (point.payload or {}).get("user_id") == user_id
            ]
        return SimpleNamespace(points=points[:limit])


def test_get_memories_paginated_sorts_newest_first():
    client = Mock()
    client.count.return_value = SimpleNamespace(count=2)
    points = [
        SimpleNamespace(
            id="older",
            payload={
                "id": "older",
                "memory": "a",
                "created_at": "2026-03-01T10:00:00",
            },
        ),
        SimpleNamespace(
            id="newer",
            payload={
                "id": "newer",
                "memory": "b",
                "created_at": "2026-03-02T10:00:00",
            },
        ),
    ]

    with (
        patch("src.services.memory_service.scroll_all_user_points", return_value=points),
        patch("src.services.memory_service._ensure_collection"),
    ):
        memories, total = get_memories_paginated("u-1", 1, 10, client, "memories")

    assert total == 2
    assert [item["id"] for item in memories] == ["newer", "older"]


def test_add_memory_builds_point_and_returns_memory_id():
    client = Mock()

    with (
        patch("src.services.memory_service._ensure_collection"),
        patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
        patch("src.services.memory_service.uuid4", return_value="fixed-id"),
        patch("src.services.memory_service.datetime") as mock_datetime,
    ):
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2026-03-27T10:00:00"
        )
        memory_id = add_memory(
            "u-1",
            {"text": "hydrate more", "translations": {"pt-BR": "hidrate mais"}},
            client,
            "memories",
            "habit",
        )

    assert memory_id == "fixed-id"
    client.upsert.assert_called_once()


def test_get_memories_paginated_normalizes_user_email_for_filter():
    client = Mock()
    client.count.return_value = SimpleNamespace(count=0)

    with patch("src.services.memory_service._ensure_collection"):
        get_memories_paginated("  RafaColucci@Gmail.com  ", 1, 10, client, "memories")

    count_filter = client.count.call_args.kwargs["count_filter"]
    assert count_filter.must[0].match.value == "rafacolucci@gmail.com"


def test_add_memory_normalizes_user_id_in_payload():
    client = Mock()

    with (
        patch("src.services.memory_service._ensure_collection"),
        patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
        patch("src.services.memory_service.uuid4", return_value="fixed-id"),
        patch("src.services.memory_service.datetime") as mock_datetime,
    ):
        mock_datetime.utcnow.return_value.isoformat.return_value = (
            "2026-03-27T10:00:00"
        )
        add_memory(
            "  RafaColucci@Gmail.com  ",
            {"text": "hydrate more"},
            client,
            "memories",
            "habit",
        )

    upsert_point = client.upsert.call_args.kwargs["points"][0]
    assert upsert_point.payload["user_id"] == "rafacolucci@gmail.com"


def test_memory_crud_roundtrip_stays_consistent_across_service_and_tools_with_normalized_user_id():
    client = FakeQdrantClient()
    mixed_user_id = "  RafaColucci@Gmail.com  "
    from src.core.config import settings

    collection_name = settings.QDRANT_COLLECTION_NAME

    with (
        patch("src.services.memory_service._embed_text", return_value=[0.1, 0.2]),
        patch("src.services.memory_service.uuid4", return_value="mem-1"),
        patch("src.services.memory_service.datetime") as mock_service_datetime,
    ):
        mock_service_datetime.utcnow.return_value.isoformat.return_value = (
            "2026-03-27T10:00:00"
        )
        memory_id = add_memory(
            mixed_user_id,
            {"text": "hydrate more"},
            client,
            collection_name,
            "context",
        )

    memories, total = get_memories_paginated(
        mixed_user_id, 1, 10, client, collection_name
    )
    assert memory_id == "mem-1"
    assert total == 1
    assert memories[0]["user_id"] == "rafacolucci@gmail.com"
    assert memories[0]["memory"] == "hydrate more"

    with (
        patch("src.services.memory_tools._embed_text", return_value=[0.3, 0.4]),
        patch("src.services.memory_tools.datetime") as mock_tools_datetime,
    ):
        mock_tools_datetime.utcnow.return_value.isoformat.return_value = (
            "2026-03-27T11:00:00"
        )
        update_result = create_update_memory_tool(client, mixed_user_id).func(
            memory_id=memory_id,
            new_content="sleep more",
        )

    assert "✅" in update_result

    search_result = create_search_memory_tool(client, mixed_user_id).func(
        query="sleep",
        limit=5,
    )
    assert "sleep more" in search_result
    assert memory_id in search_result

    delete_result = create_delete_memory_tool(client, mixed_user_id).func(
        memory_id=memory_id
    )
    assert "✅" in delete_result

    remaining_memories, remaining_total = get_memories_paginated(
        mixed_user_id, 1, 10, client, collection_name
    )
    assert remaining_total == 0
    assert remaining_memories == []
