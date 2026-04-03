"""LangChain tools for raw data retrieval without pre-computed analytics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from src.services.memory_tools import _get_collection_name
from src.utils.qdrant_utils import scroll_all_user_points


MAX_LIMIT = 200


def _parse_iso_date(date_str: str | None, field_name: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be in YYYY-MM-DD format"
        ) from exc


def _normalize_limit(limit: int) -> int:
    return max(1, min(int(limit), MAX_LIMIT))


def _normalize_offset(offset: int) -> int:
    return max(0, int(offset))


def _serialize_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in doc.items():
        if key == "_id":
            serialized["id"] = str(value)
            continue
        serialized[key] = _serialize_value(value)
    return serialized


def _paginate_payload(
    items: list[dict[str, Any]],
    total: int,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < total,
    }


def create_get_workouts_raw_tool(database, user_email: str):
    """Create raw workout retrieval tool."""

    @tool
    def get_workouts_raw(
        start_date: str | None = None,
        end_date: str | None = None,
        exercise_name: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return raw workout logs with filters and pagination."""
        start_dt = _parse_iso_date(start_date, "start_date")
        end_dt = _parse_iso_date(end_date, "end_date")
        if end_dt:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        query: dict[str, Any] = {"user_email": user_email}
        if start_dt or end_dt:
            query["date"] = {}
            if start_dt:
                query["date"]["$gte"] = start_dt
            if end_dt:
                query["date"]["$lte"] = end_dt
        if exercise_name:
            query["exercises.name"] = exercise_name

        safe_limit = _normalize_limit(limit)
        safe_offset = _normalize_offset(offset)

        total = database.workouts_repo.collection.count_documents(query)
        docs = (
            database.workouts_repo.collection.find(query)
            .sort("date", -1)
            .skip(safe_offset)
            .limit(safe_limit)
        )
        items = [_serialize_doc(doc) for doc in docs]
        return _paginate_payload(items, total, safe_limit, safe_offset)

    return get_workouts_raw


def create_get_nutrition_raw_tool(database, user_email: str):
    """Create raw nutrition retrieval tool."""

    @tool
    def get_nutrition_raw(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return raw nutrition logs with filters and pagination."""
        start_dt = _parse_iso_date(start_date, "start_date")
        end_dt = _parse_iso_date(end_date, "end_date")
        if end_dt:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        query: dict[str, Any] = {"user_email": user_email}
        if start_dt or end_dt:
            query["date"] = {}
            if start_dt:
                query["date"]["$gte"] = start_dt
            if end_dt:
                query["date"]["$lte"] = end_dt

        safe_limit = _normalize_limit(limit)
        safe_offset = _normalize_offset(offset)

        total = database.nutrition.collection.count_documents(query)
        docs = (
            database.nutrition.collection.find(query)
            .sort("date", -1)
            .skip(safe_offset)
            .limit(safe_limit)
        )
        items = [_serialize_doc(doc) for doc in docs]
        return _paginate_payload(items, total, safe_limit, safe_offset)

    return get_nutrition_raw


def create_get_body_composition_raw_tool(database, user_email: str):
    """Create raw body composition retrieval tool."""

    @tool
    def get_body_composition_raw(
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return raw body composition logs with filters and pagination."""
        start_dt = _parse_iso_date(start_date, "start_date")
        end_dt = _parse_iso_date(end_date, "end_date")
        if end_dt:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        query: dict[str, Any] = {"user_email": user_email}
        if start_dt or end_dt:
            query["date"] = {}
            if start_dt:
                query["date"]["$gte"] = start_dt
            if end_dt:
                query["date"]["$lte"] = end_dt

        safe_limit = _normalize_limit(limit)
        safe_offset = _normalize_offset(offset)

        total = database.weight.collection.count_documents(query)
        docs = (
            database.weight.collection.find(query)
            .sort("date", -1)
            .skip(safe_offset)
            .limit(safe_limit)
        )
        items = [_serialize_doc(doc) for doc in docs]
        return _paginate_payload(items, total, safe_limit, safe_offset)

    return get_body_composition_raw


def create_get_goal_history_raw_tool(database, user_email: str):
    """Create goal history raw retrieval tool."""

    @tool
    def get_goal_history_raw() -> dict[str, Any]:
        """Return raw goal history snapshots from profile data."""
        profile = database.get_user_profile(user_email)
        if not profile:
            return _paginate_payload([], 0, 0, 0)

        history = getattr(profile, "goal_history", None) or []
        if not history:
            history = [
                {
                    "goal_type": getattr(profile, "goal_type", None),
                    "weekly_rate": getattr(profile, "weekly_rate", None),
                    "target_weight": getattr(profile, "target_weight", None),
                    "recorded_at": getattr(profile, "tdee_last_check_in", None),
                    "source": "profile_snapshot",
                }
            ]

        items = [_serialize_doc(item) for item in history]
        return _paginate_payload(items, len(items), len(items), 0)

    return get_goal_history_raw


def create_get_events_raw_tool(database, user_email: str):
    """Create events raw retrieval tool."""

    @tool
    def get_events_raw(
        start_date: str | None = None,
        end_date: str | None = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return raw scheduled events with filters and pagination."""
        start_dt = _parse_iso_date(start_date, "start_date")
        end_dt = _parse_iso_date(end_date, "end_date")

        query: dict[str, Any] = {"user_email": user_email}
        if active_only:
            query["active"] = True

        # Events are stored with date as YYYY-MM-DD string (or None)
        if start_dt or end_dt:
            date_query: dict[str, Any] = {}
            if start_dt:
                date_query["$gte"] = start_dt.strftime("%Y-%m-%d")
            if end_dt:
                date_query["$lte"] = end_dt.strftime("%Y-%m-%d")
            query["date"] = date_query

        safe_limit = _normalize_limit(limit)
        safe_offset = _normalize_offset(offset)

        events_collection = database.database.events
        total = events_collection.count_documents(query)
        docs = events_collection.find(query).sort("date", 1).skip(safe_offset).limit(safe_limit)

        items = [_serialize_doc(doc) for doc in docs]
        return _paginate_payload(items, total, safe_limit, safe_offset)

    return get_events_raw


def create_get_memories_raw_tool(qdrant_client, user_email: str):
    """Create raw memories retrieval tool."""

    def _parse_created_datetime(payload: dict[str, Any]) -> datetime | None:
        created_at = payload.get("created_at")
        if not created_at:
            return None
        try:
            return datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        except ValueError:
            return None

    def _matches_filters(
        payload: dict[str, Any],
        category: str | None,
        start_dt: datetime | None,
        end_dt: datetime | None,
    ) -> bool:
        if category and payload.get("category") != category:
            return False
        created_dt = _parse_created_datetime(payload)
        if start_dt and created_dt and created_dt < start_dt:
            return False
        if end_dt and created_dt and created_dt > end_dt:
            return False
        return True

    def _memory_item(point_id: str | int, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": payload.get("id", str(point_id)),
            "memory": payload.get("memory", ""),
            "category": payload.get("category"),
            "created_at": payload.get("created_at"),
            "updated_at": payload.get("updated_at"),
            "user_id": payload.get("user_id"),
        }

    @tool
    def get_memories_raw(
        category: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Return raw memories with category/date filters and pagination."""
        from qdrant_client import models as qdrant_models  # pylint: disable=import-outside-toplevel

        start_dt = _parse_iso_date(start_date, "start_date")
        end_dt = _parse_iso_date(end_date, "end_date")
        if end_dt:
            end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        collection_name = _get_collection_name(user_email)
        user_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="user_id", match=qdrant_models.MatchValue(value=user_email)
                )
            ]
        )

        all_points = scroll_all_user_points(qdrant_client, collection_name, user_filter)

        items = [
            _memory_item(point.id, point.payload or {})
            for point in all_points
            if _matches_filters(point.payload or {}, category, start_dt, end_dt)
        ]

        items.sort(key=lambda item: item.get("created_at") or "", reverse=True)

        safe_limit = _normalize_limit(limit)
        safe_offset = _normalize_offset(offset)
        paged_items = items[safe_offset : safe_offset + safe_limit]

        return _paginate_payload(paged_items, len(items), safe_limit, safe_offset)

    return get_memories_raw
