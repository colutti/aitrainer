"""Tests for admin-side demo user protection and pruning."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from src.api.endpoints.admin_users import (
    delete_demo_episode,
    delete_demo_message,
    delete_user,
    get_demo_episode,
    get_user_details,
    list_users,
    update_user,
)


def _build_cursor(items: list[dict]):
    """Build a minimal cursor mock matching pymongo chaining."""
    cursor = MagicMock()
    cursor.skip.return_value = cursor
    cursor.limit.return_value = items
    cursor.sort.return_value = items
    cursor.__iter__.return_value = iter(items)
    return cursor


def test_list_users_keeps_demo_flag_visible():
    """Admin list should expose demo flag for UI protection."""
    user_doc = {"email": "demo@test.com", "is_demo": True, "role": "user"}
    db = SimpleNamespace(users=MagicMock())
    db.users.find.return_value = _build_cursor([user_doc])
    db.users.count_documents.return_value = 1

    response = list_users({"email": "admin@test.com"}, db, 1, 20, None)

    assert response["users"][0]["is_demo"] is True


def test_get_user_details_includes_demo_snapshot_and_episodes():
    db = SimpleNamespace(
        users=MagicMock(),
        message_store=MagicMock(),
        workout_logs=MagicMock(),
        nutrition_logs=MagicMock(),
        demo_snapshots=MagicMock(),
        demo_episodes=MagicMock(),
        demo_messages=MagicMock(),
    )
    db.users.find_one.return_value = {"email": "demo@test.com", "is_demo": True}
    db.message_store.count_documents.return_value = 5
    db.workout_logs.count_documents.return_value = 2
    db.nutrition_logs.count_documents.return_value = 3
    db.demo_snapshots.find_one.return_value = {"snapshot_id": "snap-1", "demo_email": "demo@test.com"}
    db.demo_episodes.find.return_value = _build_cursor(
        [{"episode_id": "ep-1", "status": "published", "demo_email": "demo@test.com"}]
    )
    db.demo_messages.count_documents.return_value = 2

    response = get_user_details("demo@test.com", {"email": "admin@test.com"}, db)

    assert response["demo_snapshot"]["snapshot_id"] == "snap-1"
    assert response["demo_episodes"][0]["episode_id"] == "ep-1"


def test_update_user_rejects_demo_target():
    """Admin cannot update a protected demo user."""
    db = SimpleNamespace(users=MagicMock())
    db.users.find_one.return_value = {"email": "demo@test.com", "is_demo": True}

    with pytest.raises(HTTPException) as exc_info:
        update_user("demo@test.com", {"subscription_plan": "Pro"}, {"email": "admin@test.com"}, db)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "demo_read_only"
    db.users.update_one.assert_not_called()


def test_delete_user_rejects_demo_target():
    """Admin cannot delete a protected demo user."""
    db = SimpleNamespace(
        users=MagicMock(),
        trainer_profiles=MagicMock(),
        message_store=MagicMock(),
        workout_logs=MagicMock(),
        nutrition_logs=MagicMock(),
        weight_logs=MagicMock(),
        prompt_logs=MagicMock(),
    )
    db.users.find_one.return_value = {"email": "demo@test.com", "is_demo": True, "role": "user"}

    with pytest.raises(HTTPException) as exc_info:
        delete_user("demo@test.com", {"email": "admin@test.com"}, db)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "demo_read_only"
    db.users.delete_one.assert_not_called()


def test_get_demo_episode_returns_messages():
    db = SimpleNamespace(
        demo_episodes=MagicMock(),
        demo_messages=MagicMock(),
    )
    db.demo_episodes.find_one.return_value = {
        "episode_id": "ep-1",
        "status": "published",
        "demo_email": "demo@test.com",
    }
    db.demo_messages.find.return_value = _build_cursor(
        [{"message_id": "msg-1", "status": "published"}]
    )

    response = get_demo_episode("demo@test.com", "ep-1", {"email": "admin@test.com"}, db)

    assert response["episode"]["episode_id"] == "ep-1"
    assert response["messages"][0]["message_id"] == "msg-1"


def test_delete_demo_episode_removes_metadata_and_message_store():
    db = SimpleNamespace(
        demo_episodes=MagicMock(),
        demo_messages=MagicMock(),
        message_store=MagicMock(),
        demo_prune_log=MagicMock(),
    )
    db.demo_episodes.find_one.return_value = {
        "episode_id": "ep-1",
        "demo_email": "demo@test.com",
        "snapshot_id": "snap-1",
        "published_message_ids": ["msg-1", "msg-2"],
    }

    response = delete_demo_episode("demo@test.com", "ep-1", {"email": "admin@test.com"}, db)

    assert response["message"] == "Demo episode deleted successfully"
    db.demo_messages.delete_many.assert_called_once()
    db.message_store.delete_many.assert_called_once()
    db.demo_prune_log.insert_one.assert_called_once()


def test_delete_demo_message_removes_single_message():
    db = SimpleNamespace(
        demo_messages=MagicMock(),
        message_store=MagicMock(),
        demo_episodes=MagicMock(),
        demo_prune_log=MagicMock(),
    )
    db.demo_messages.find_one.return_value = {
        "message_id": "msg-1",
        "episode_id": "ep-1",
        "snapshot_id": "snap-1",
        "demo_email": "demo@test.com",
    }
    db.demo_episodes.find_one.return_value = {"published_message_ids": []}

    response = delete_demo_message("demo@test.com", "msg-1", {"email": "admin@test.com"}, db)

    assert response["message"] == "Demo message deleted successfully"
    db.demo_messages.delete_one.assert_called_once()
    db.message_store.delete_many.assert_called_once()
    db.demo_episodes.update_one.assert_called_once()
    db.demo_episodes.delete_one.assert_called_once()
    db.demo_prune_log.insert_one.assert_called_once()
