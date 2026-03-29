from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.services.memory_service import add_memory, get_memories_paginated


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
