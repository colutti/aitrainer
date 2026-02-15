"""
Unit tests for tool_registry module.
"""

from src.services.tool_registry import (
    is_tool_ephemeral,
    should_store_memory,
)


class TestIsToolEphemeral:
    def test_get_workouts_is_ephemeral(self):
        assert is_tool_ephemeral("get_workouts") is True

    def test_save_workout_is_not_ephemeral(self):
        assert is_tool_ephemeral("save_workout") is False

    def test_unknown_tool_defaults_to_memorable(self):
        assert is_tool_ephemeral("unknown_tool") is False

    def test_search_memory_is_ephemeral(self):
        assert is_tool_ephemeral("search_memory") is True

    def test_save_memory_is_memorable(self):
        assert is_tool_ephemeral("save_memory") is False

    def test_update_memory_is_memorable(self):
        assert is_tool_ephemeral("update_memory") is False

    def test_delete_memory_is_memorable(self):
        assert is_tool_ephemeral("delete_memory") is False


class TestShouldStoreMemory:
    def test_no_tools_should_store(self):
        assert should_store_memory([]) is True

    def test_only_ephemeral_tools_should_skip(self):
        assert should_store_memory(["get_workouts", "get_nutrition"]) is False

    def test_memorable_tool_should_store(self):
        assert should_store_memory(["save_workout"]) is True

    def test_mixed_tools_should_store(self):
        assert should_store_memory(["get_workouts", "save_workout"]) is True

    def test_search_memory_only_should_skip(self):
        """search_memory is ephemeral, so only it should skip storage."""
        assert should_store_memory(["search_memory"]) is False

    def test_save_memory_should_store(self):
        """save_memory is memorable, should trigger storage."""
        assert should_store_memory(["save_memory"]) is True

    def test_memory_tools_mixed_should_store(self):
        """Any memorable memory tool should trigger storage."""
        assert should_store_memory(["search_memory", "save_memory"]) is True
        assert should_store_memory(["search_memory", "update_memory"]) is True
        assert should_store_memory(["search_memory", "delete_memory"]) is True
