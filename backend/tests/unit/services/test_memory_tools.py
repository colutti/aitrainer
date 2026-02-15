"""
Unit tests for AI-driven memory management tools.

Note: These are simplified integration tests that verify the tools work correctly
when integrated with the rest of the system. Full mocking of LangChain tools
is complex due to the @tool decorator behavior.
"""

from unittest.mock import MagicMock

from src.services.memory_tools import _get_collection_name


class TestGetCollectionName:
    """Tests for _get_collection_name helper."""

    def test_returns_base_collection_name(self):
        """Test that collection name returns base collection (shared across all users)."""
        from src.core.config import settings

        result = _get_collection_name("user@test.com")
        # Should return the base collection name, not per-user
        assert result == settings.QDRANT_COLLECTION_NAME

    def test_returns_same_collection_for_different_users(self):
        """Test that all users share the same collection (filtered by user_id in payload)."""
        result1 = _get_collection_name("user1@test.com")
        result2 = _get_collection_name("user2@test.com")
        # Both should return the same collection name
        assert result1 == result2

    def test_collection_name_ignores_email_parameter(self):
        """Test that the user_email parameter is ignored (not used for collection naming)."""
        from src.core.config import settings

        result = _get_collection_name("anything@example.com")
        # Email should not affect result - should always return base collection
        assert result == settings.QDRANT_COLLECTION_NAME


class TestMemoryToolsIntegration:
    """Integration tests for memory tools.

    Note: Due to LangChain's @tool decorator creating StructuredTool objects,
    these tests are simplified to verify the factory functions exist and
    can be called. Full tool invocation testing is done via E2E tests.
    """

    def test_save_memory_tool_creation(self):
        """Test that save_memory_tool can be created."""
        from src.services.memory_tools import create_save_memory_tool

        mock_qdrant = MagicMock()
        mock_mem0 = MagicMock()
        tool = create_save_memory_tool(mock_qdrant, "test@example.com", mock_mem0)

        # Tool should exist and have a name
        assert tool is not None
        assert hasattr(tool, 'name')
        assert 'save' in tool.name.lower() or 'memory' in tool.name.lower()

    def test_search_memory_tool_creation(self):
        """Test that search_memory_tool can be created."""
        from src.services.memory_tools import create_search_memory_tool

        mock_qdrant = MagicMock()
        mock_mem0 = MagicMock()
        tool = create_search_memory_tool(mock_qdrant, "test@example.com", mock_mem0)

        assert tool is not None
        assert hasattr(tool, 'name')

    def test_update_memory_tool_creation(self):
        """Test that update_memory_tool can be created."""
        from src.services.memory_tools import create_update_memory_tool

        mock_qdrant = MagicMock()
        mock_mem0 = MagicMock()
        tool = create_update_memory_tool(mock_qdrant, "test@example.com", mock_mem0)

        assert tool is not None
        assert hasattr(tool, 'name')

    def test_delete_memory_tool_creation(self):
        """Test that delete_memory_tool can be created."""
        from src.services.memory_tools import create_delete_memory_tool

        mock_qdrant = MagicMock()
        mock_mem0 = MagicMock()
        tool = create_delete_memory_tool(mock_qdrant, "test@example.com", mock_mem0)

        assert tool is not None
        assert hasattr(tool, 'name')
