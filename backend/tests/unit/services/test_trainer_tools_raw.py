"""Tests for raw data tools registration in AITrainerBrain."""

from unittest.mock import MagicMock

from src.services.trainer import AITrainerBrain


def test_get_tools_includes_raw_data_tools():
    db = MagicMock()
    llm = MagicMock()
    db.get_user_profile.return_value = None

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
    db.get_user_profile.return_value = None

    brain = AITrainerBrain(database=db, llm_client=llm, qdrant_client=qdrant)

    tools = brain.get_tools("test@example.com")
    names = {tool.name for tool in tools}

    assert "get_memories_raw" in names


def test_get_tools_does_not_include_hevy_tools_when_disabled():
    """Hevy tools must NOT be exposed when user has hevy_enabled=False or no api_key."""
    from unittest.mock import MagicMock
    from src.api.models.user_profile import UserProfile

    db = MagicMock()
    llm = MagicMock()
    profile = MagicMock(spec=UserProfile)
    profile.hevy_enabled = False
    profile.hevy_api_key = None
    db.get_user_profile.return_value = profile

    brain = AITrainerBrain(database=db, llm_client=llm)

    tools = brain.get_tools("test@example.com")
    hevy_names = {t.name for t in tools if "hevy" in t.name}

    assert len(hevy_names) == 0, f"Expected no Hevy tools, got: {hevy_names}"


def test_get_tools_includes_hevy_tools_when_enabled():
    """Hevy tools must be exposed when user has hevy_enabled=True and api_key."""
    from unittest.mock import MagicMock
    from src.api.models.user_profile import UserProfile

    db = MagicMock()
    llm = MagicMock()
    profile = MagicMock(spec=UserProfile)
    profile.hevy_enabled = True
    profile.hevy_api_key = "valid-key-123"
    db.get_user_profile.return_value = profile

    brain = AITrainerBrain(database=db, llm_client=llm)

    tools = brain.get_tools("test@example.com")
    hevy_names = {t.name for t in tools if "hevy" in t.name}

    assert len(hevy_names) > 0, "Expected Hevy tools, got none"
    assert "list_hevy_routines" in hevy_names
    assert "create_hevy_routine" in hevy_names
    assert "trigger_hevy_import" in hevy_names


def test_get_tools_includes_plan_training_program_tool():
    """get_plan_training_program must always be available."""
    from unittest.mock import MagicMock

    db = MagicMock()
    llm = MagicMock()
    db.get_user_profile.return_value = None

    brain = AITrainerBrain(database=db, llm_client=llm)

    tools = brain.get_tools("test@example.com")
    names = {t.name for t in tools}

    assert "get_plan_training_program" in names
