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
        tool = create_save_memory_tool(mock_qdrant, "test@example.com")

        # Tool should exist and have a name
        assert tool is not None
        assert hasattr(tool, 'name')
        assert 'save' in tool.name.lower() or 'memory' in tool.name.lower()

    def test_save_memory_returns_duplicate_warning_when_similar_exists(self):
        """Test that save_memory detects duplicates and returns warning without creating new."""
        from src.services.memory_tools import create_save_memory_tool
        from unittest.mock import patch
        from qdrant_client.models import PointStruct

        mock_qdrant = MagicMock()

        # Mock similar memory detection
        existing_point = PointStruct(
            id="existing-id",
            vector=[0.1] * 768,
            payload={
                "id": "existing-id",
                "memory": "eu malho segunda, terça, quarta",
                "user_id": "test@example.com",
                "category": "context"
            }
        )
        mock_qdrant.query_points.return_value = MagicMock(points=[existing_point])

        # Mock embedding function to return a 768-dim vector
        with patch('src.services.memory_tools._embed_text') as mock_embed:
            mock_embed.return_value = [0.1] * 768

            tool = create_save_memory_tool(mock_qdrant, "test@example.com")
            result = tool.func(content="eu malho segunda, terça, quarta", category="context")

        # Should return warning about duplicate
        assert "similar" in result.lower() or "já existe" in result.lower() or "⚠️" in result
        # Should NOT have called upsert
        mock_qdrant.upsert.assert_not_called()

    def test_save_memory_saves_when_no_similar_exists(self):
        """Test that save_memory creates new memory when no similar exists."""
        from src.services.memory_tools import create_save_memory_tool
        from unittest.mock import patch

        mock_qdrant = MagicMock()

        # Mock no similar memories found
        mock_qdrant.query_points.return_value = MagicMock(points=[])

        # Mock embedding function
        with patch('src.services.memory_tools._embed_text') as mock_embed:
            mock_embed.return_value = [0.2] * 768

            tool = create_save_memory_tool(mock_qdrant, "test@example.com")
            result = tool.func(content="nova informação", category="preference")

        # Should return success message
        assert "✅" in result or "salva" in result.lower()
        # Should have called upsert
        mock_qdrant.upsert.assert_called_once()

    def test_search_memory_tool_creation(self):
        """Test that search_memory_tool can be created."""
        from src.services.memory_tools import create_search_memory_tool

        mock_qdrant = MagicMock()
        tool = create_search_memory_tool(mock_qdrant, "test@example.com")

        assert tool is not None
        assert hasattr(tool, 'name')

    def test_update_memory_tool_creation(self):
        """Test that update_memory_tool can be created."""
        from src.services.memory_tools import create_update_memory_tool

        mock_qdrant = MagicMock()
        tool = create_update_memory_tool(mock_qdrant, "test@example.com")

        assert tool is not None
        assert hasattr(tool, 'name')

    def test_delete_memory_tool_creation(self):
        """Test that delete_memory_tool can be created."""
        from src.services.memory_tools import create_delete_memory_tool

        mock_qdrant = MagicMock()
        tool = create_delete_memory_tool(mock_qdrant, "test@example.com")

        assert tool is not None
        assert hasattr(tool, 'name')
