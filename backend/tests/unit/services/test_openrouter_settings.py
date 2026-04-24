"""Tests for OpenRouter settings loading."""

import unittest
from unittest.mock import patch

from pydantic import ValidationError

from src.core.config import Settings


class TestOpenRouterSettings(unittest.TestCase):
    """Test suite for OpenRouter-specific environment settings."""

    def test_settings_load_openrouter_fields(self):
        """Verify OpenRouter settings are loaded from environment."""
        with patch.dict(
            "os.environ",
            {
                "OPENROUTER_API_KEY": "or-test",
                "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                "OPENROUTER_CHAT_MODEL": "@preset/fityq-chat",
                "OPENROUTER_EMBED_MODEL": "openai/text-embedding-3-small",
                "OPENROUTER_EMBED_DIMENSIONS": "768",
                "SECRET_KEY": "test",
                "API_SERVER_PORT": "8000",
                "MAX_SHORT_TERM_MEMORY_MESSAGES": "10",
                "MAX_LONG_TERM_MEMORY_MESSAGES": "10",
                "DB_NAME": "test",
                "MONGO_URI": "mongodb://user:pass@localhost:27017/",
                "RUNNING_IN_CONTAINER": "true",
                "QDRANT_HOST": "localhost",
                "QDRANT_PORT": "6333",
                "QDRANT_COLLECTION_NAME": "test",
                "QDRANT_API_KEY": "test",
            },
        ):
            settings = Settings()

            self.assertEqual(settings.OPENROUTER_API_KEY, "or-test")
            self.assertEqual(settings.OPENROUTER_CHAT_MODEL, "@preset/fityq-chat")
            self.assertEqual(
                settings.OPENROUTER_EMBED_MODEL, "openai/text-embedding-3-small"
            )
            self.assertEqual(settings.OPENROUTER_EMBED_DIMENSIONS, 768)

    def test_settings_reject_non_preset_chat_model(self):
        """Verify OPENROUTER_CHAT_MODEL rejects non-preset values."""
        with patch.dict(
            "os.environ",
            {
                "OPENROUTER_API_KEY": "or-test",
                "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                "OPENROUTER_CHAT_MODEL": "openai/gpt-4o-mini",
                "OPENROUTER_EMBED_MODEL": "openai/text-embedding-3-small",
                "OPENROUTER_EMBED_DIMENSIONS": "768",
                "SECRET_KEY": "test",
                "DB_NAME": "test",
                "MONGO_URI": "mongodb://localhost:27017",
                "RUNNING_IN_CONTAINER": "true",
                "QDRANT_HOST": "localhost",
                "QDRANT_PORT": "6333",
                "QDRANT_COLLECTION_NAME": "test",
                "QDRANT_API_KEY": "test",
            },
            clear=True,
        ):
            with self.assertRaises(ValidationError):
                Settings()


if __name__ == "__main__":
    unittest.main()
