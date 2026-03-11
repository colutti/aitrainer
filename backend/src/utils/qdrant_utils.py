"""Utility functions for Qdrant operations."""
from typing import List, Any
from qdrant_client import QdrantClient, models as qdrant_models


def scroll_all_user_points(
    qdrant_client: QdrantClient,
    collection_name: str,
    user_filter: qdrant_models.Filter,
) -> List[Any]:
    """Scrolls through all points for a given filter in Qdrant."""
    all_points = []
    next_offset = None

    while True:
        points, next_offset = qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=user_filter,
            limit=100,
            offset=next_offset,
            with_payload=True,
        )
        all_points.extend(points)
        if next_offset is None:
            break

    return all_points


def point_to_dict(point: Any) -> dict:
    """Converts a Qdrant point to a standard memory dictionary."""
    payload = point.payload or {}
    return {
        "id": payload.get("id", str(point.id)),
        "memory": payload.get("memory", payload.get("data", "")),
        "user_id": payload.get("user_id"),
        "created_at": payload.get("created_at"),
        "updated_at": payload.get("updated_at"),
    }
