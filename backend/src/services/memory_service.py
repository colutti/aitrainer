"""Service for managing memories in Qdrant."""
from typing import List, Dict, Any, Tuple
from qdrant_client import QdrantClient, models as qdrant_models
from src.core.logs import logger
from src.utils.qdrant_utils import scroll_all_user_points, point_to_dict

def get_memories_paginated(
    user_id: str,
    page: int,
    page_size: int,
    qdrant_client: QdrantClient,
    collection_name: str,
) -> Tuple[List[Dict[str, Any]], int]:
    """Retrieves memories for a user with pagination via Qdrant scroll."""
    logger.info(
        "Retrieving paginated memories for user: %s (page: %d, size: %d)",
        user_id, page, page_size
    )

    try:
        user_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="user_id", match=qdrant_models.MatchValue(value=user_id)
                )
            ]
        )

        total = qdrant_client.count(
            collection_name=collection_name, count_filter=user_filter
        ).count

        if total == 0:
            return [], 0

        all_points = scroll_all_user_points(qdrant_client, collection_name, user_filter)

        offset = (page - 1) * page_size

        all_points.sort(
            key=lambda p: p.payload.get("created_at", "") if p.payload else "",
            reverse=True
        )

        memories = [point_to_dict(point) for point in all_points[offset:offset + page_size]]

        return memories, total

    except (ValueError, TypeError, AttributeError) as e:
        logger.error("Failed to retrieve paginated memories: %s", e)
        raise
