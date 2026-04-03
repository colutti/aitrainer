"""Tests for admin prompt listing/details enrichments."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from src.api.endpoints.admin_prompts import list_prompts, get_prompt_details


def _build_cursor(items: list[dict]):
    cursor = MagicMock()
    cursor.sort.return_value = cursor
    cursor.skip.return_value = cursor
    cursor.limit.return_value = items
    return cursor


def test_list_prompts_adds_prompt_format_and_raw_tools_fields():
    docs = [
        {
            "_id": "abc",
            "timestamp": "2026-04-03T10:00:00",
            "user_email": "test@example.com",
            "prompt": {
                "prompt": "# FityQ AI\n\nBody",
                "tools_called": ["get_workouts_raw", "get_nutrition", "get_nutrition_raw"],
                "messages": [{"role": "system", "content": "x"}],
            },
        }
    ]
    db = SimpleNamespace(prompt_logs=MagicMock())
    db.prompt_logs.find.return_value = _build_cursor(docs)
    db.prompt_logs.count_documents.return_value = 1

    resp = list_prompts({"email": "admin@test.com"}, db, None, 1, 20)

    prompt = resp["prompts"][0]
    assert prompt["prompt_format"] == "markdown"
    assert prompt["raw_tools_called_count"] == 2
    assert "get_workouts_raw" in prompt["raw_tools_called"]


def test_get_prompt_details_adds_prompt_format_and_raw_tools_fields():
    db = SimpleNamespace(prompt_logs=MagicMock())
    db.prompt_logs.find_one.return_value = {
        "_id": "abc",
        "prompt": {
            "prompt": "# FityQ AI\n\nBody",
            "tools_called": ["get_workouts_raw"],
        },
    }

    resp = get_prompt_details("507f1f77bcf86cd799439011", {"email": "admin@test.com"}, db)

    assert resp["prompt_format"] == "markdown"
    assert resp["raw_tools_called_count"] == 1
    assert resp["raw_tools_called"] == ["get_workouts_raw"]
