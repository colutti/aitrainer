"""Tests for raw data tools registration in AITrainerBrain."""

from unittest.mock import MagicMock, patch

from src.services.trainer import AITrainerBrain


def test_get_tools_includes_raw_data_tools():
    db = MagicMock()
    llm = MagicMock()

    with patch("src.services.trainer.HistoryCompactor"):
        brain = AITrainerBrain(database=db, llm_client=llm)

    tools = brain.get_tools("test@example.com")
    names = {tool.name for tool in tools}

    assert "get_workouts_raw" in names
    assert "get_nutrition_raw" in names
    assert "get_body_composition_raw" in names
    assert "get_goal_history_raw" in names
    assert "get_events_raw" in names


def test_get_tools_includes_raw_memories_tool_when_qdrant_is_available():
    db = MagicMock()
    llm = MagicMock()
    qdrant = MagicMock()

    with patch("src.services.trainer.HistoryCompactor"):
        brain = AITrainerBrain(database=db, llm_client=llm, qdrant_client=qdrant)

    tools = brain.get_tools("test@example.com")
    names = {tool.name for tool in tools}

    assert "get_memories_raw" in names
