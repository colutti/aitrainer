"""Unit tests for raw data tools (TDD RED->GREEN)."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.services.raw_data_tools import (
    create_get_workouts_raw_tool,
    create_get_nutrition_raw_tool,
    create_get_body_composition_raw_tool,
    create_get_goal_history_raw_tool,
    create_get_events_raw_tool,
    create_get_memories_raw_tool,
)


def _fake_point(payload: dict, point_id: str = "p1"):
    return SimpleNamespace(payload=payload, id=point_id)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.database = MagicMock()

    db.workouts_repo.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
        {
            "_id": "w1",
            "user_email": "test@example.com",
            "date": datetime(2026, 1, 10, 8, 0, 0),
            "workout_type": "Upper",
            "exercises": [{"name": "Bench", "sets": 3, "reps_per_set": [10, 8, 6]}],
        }
    ]
    db.workouts_repo.collection.count_documents.return_value = 1

    db.nutrition.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
        {
            "_id": "n1",
            "user_email": "test@example.com",
            "date": datetime(2026, 1, 10, 0, 0, 0),
            "calories": 2200,
            "protein_grams": 160.0,
            "carbs_grams": 220.0,
            "fat_grams": 70.0,
        }
    ]
    db.nutrition.collection.count_documents.return_value = 1

    db.weight.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
        {
            "_id": "c1",
            "user_email": "test@example.com",
            "date": datetime(2026, 1, 10, 0, 0, 0),
            "weight": 82.3,
            "body_fat": 18.4,
        }
    ]
    db.weight.collection.count_documents.return_value = 1

    db.database.events.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
        {
            "_id": "e1",
            "user_email": "test@example.com",
            "title": "Check-in",
            "date": "2026-01-20",
            "active": True,
            "recurrence": "weekly",
        }
    ]
    db.database.events.count_documents.return_value = 1

    db.get_user_profile.return_value = SimpleNamespace(
        goal_type="lose",
        weekly_rate=0.5,
        target_weight=75.0,
        tdee_last_check_in="2026-01-10",
    )
    return db


def test_get_workouts_raw_returns_structured_payload(mock_db):
    tool = create_get_workouts_raw_tool(mock_db, "test@example.com")

    result = tool.func(start_date="2026-01-01", end_date="2026-01-31", limit=20, offset=0)

    assert result["total"] == 1
    assert result["limit"] == 20
    assert result["offset"] == 0
    assert result["items"][0]["workout_type"] == "Upper"


def test_get_nutrition_raw_returns_structured_payload(mock_db):
    tool = create_get_nutrition_raw_tool(mock_db, "test@example.com")

    result = tool.func(start_date="2026-01-01", end_date="2026-01-31", limit=20, offset=0)

    assert result["total"] == 1
    assert result["items"][0]["calories"] == 2200


def test_get_body_composition_raw_returns_structured_payload(mock_db):
    tool = create_get_body_composition_raw_tool(mock_db, "test@example.com")

    result = tool.func(start_date="2026-01-01", end_date="2026-01-31", limit=20, offset=0)

    assert result["total"] == 1
    assert result["items"][0]["weight"] == 82.3


def test_get_goal_history_raw_returns_snapshot_when_no_history(mock_db):
    tool = create_get_goal_history_raw_tool(mock_db, "test@example.com")

    result = tool.func()

    assert result["total"] == 1
    assert result["items"][0]["goal_type"] == "lose"


def test_get_events_raw_returns_structured_payload(mock_db):
    tool = create_get_events_raw_tool(mock_db, "test@example.com")

    result = tool.func(start_date="2026-01-01", end_date="2026-01-31", active_only=True, limit=20, offset=0)

    assert result["total"] == 1
    assert result["items"][0]["title"] == "Check-in"


def test_get_memories_raw_returns_structured_payload_with_filters(mock_db):
    qdrant = MagicMock()
    point = _fake_point(
        {
            "id": "m1",
            "memory": "Prefere treinar cedo",
            "category": "preference",
            "created_at": "2026-01-10T10:00:00",
            "updated_at": "2026-01-10T10:00:00",
            "user_id": "test@example.com",
        }
    )

    with patch("src.services.raw_data_tools.scroll_all_user_points", return_value=[point]):
        tool = create_get_memories_raw_tool(qdrant, "test@example.com")
        result = tool.func(category="preference", limit=10, offset=0)

    assert result["total"] == 1
    assert result["items"][0]["category"] == "preference"


def test_get_workouts_raw_validates_date_format(mock_db):
    tool = create_get_workouts_raw_tool(mock_db, "test@example.com")

    with pytest.raises(ValueError):
        tool.func(start_date="10-01-2026")
