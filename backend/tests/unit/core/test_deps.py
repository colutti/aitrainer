"""
Tests for dependency injection functions in src/core/deps.py
"""

from unittest.mock import patch, MagicMock
from src.core.deps import (
    get_mem0_client,
    get_qdrant_client,
    get_llm_client,
    get_mongo_database,
    get_ai_trainer_brain,
)


def test_get_mem0_client():
    """Test that get_mem0_client returns a Memory instance."""
    # Clear cache before test
    get_mem0_client.cache_clear()

    with patch("src.core.deps.Memory.from_config") as mock_memory:
        mock_memory.return_value = MagicMock()

        client = get_mem0_client()

        assert client is not None
        mock_memory.assert_called_once()

        # Test caching - should not call from_config again
        client2 = get_mem0_client()
        assert client is client2
        assert mock_memory.call_count == 1


def test_get_qdrant_client_with_url():
    """Test get_qdrant_client when QDRANT_HOST is a URL."""
    get_qdrant_client.cache_clear()

    with (
        patch("src.core.deps.settings") as mock_settings,
        patch("src.core.deps.QdrantClient") as mock_qdrant,
    ):
        mock_settings.QDRANT_HOST = "https://qdrant.example.com"
        mock_settings.QDRANT_PORT = 6333
        mock_settings.QDRANT_API_KEY = "test-key"

        mock_qdrant.return_value = MagicMock()

        client = get_qdrant_client()

        assert client is not None
        mock_qdrant.assert_called_once()
        call_kwargs = mock_qdrant.call_args[1]
        assert "url" in call_kwargs
        assert call_kwargs["api_key"] == "test-key"


def test_get_qdrant_client_local():
    """Test get_qdrant_client for local/self-hosted setup."""
    get_qdrant_client.cache_clear()

    with (
        patch("src.core.deps.settings") as mock_settings,
        patch("src.core.deps.QdrantClient") as mock_qdrant,
    ):
        mock_settings.QDRANT_HOST = "localhost"
        mock_settings.QDRANT_PORT = 6333

        mock_qdrant.return_value = MagicMock()

        client = get_qdrant_client()

        assert client is not None
        mock_qdrant.assert_called_once()
        call_kwargs = mock_qdrant.call_args[1]
        assert call_kwargs["host"] == "localhost"
        assert call_kwargs["port"] == 6333


def test_get_llm_client():
    """Test that get_llm_client returns an LLMClient instance."""
    get_llm_client.cache_clear()

    with patch("src.core.deps.LLMClient.from_config") as mock_llm:
        mock_llm.return_value = MagicMock()

        client = get_llm_client()

        assert client is not None
        mock_llm.assert_called_once()


def test_get_mongo_database():
    """Test that get_mongo_database returns a MongoDatabase instance."""
    get_mongo_database.cache_clear()

    with patch("src.core.deps.MongoDatabase") as mock_mongo:
        mock_mongo.return_value = MagicMock()

        db = get_mongo_database()

        assert db is not None
        mock_mongo.assert_called_once()


def test_get_ai_trainer_brain():
    """Test that get_ai_trainer_brain creates AITrainerBrain with dependencies."""
    # Clear all caches
    get_llm_client.cache_clear()
    get_mem0_client.cache_clear()
    get_mongo_database.cache_clear()
    get_ai_trainer_brain.cache_clear()

    with (
        patch("src.core.deps.LLMClient.from_config") as mock_llm,
        patch("src.core.deps.Memory.from_config") as mock_mem0,
        patch("src.core.deps.MongoDatabase") as mock_mongo,
        patch("src.core.deps.AITrainerBrain") as mock_brain,
    ):
        mock_llm.return_value = MagicMock()
        mock_mem0.return_value = MagicMock()
        mock_mongo.return_value = MagicMock()
        mock_brain.return_value = MagicMock()

        brain = get_ai_trainer_brain()

        assert brain is not None
        mock_brain.assert_called_once()
        call_kwargs = mock_brain.call_args[1]
        assert "llm_client" in call_kwargs
        assert "memory" in call_kwargs
        assert "database" in call_kwargs
