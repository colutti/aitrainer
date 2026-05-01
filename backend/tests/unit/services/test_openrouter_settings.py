"""Tests for OpenRouter settings loading."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.config import Settings, validate_required_runtime_config


class TestOpenRouterSettings(unittest.TestCase):
    """Test suite for OpenRouter-specific environment settings."""

    def test_settings_load_openrouter_fields(self):
        """Verify OpenRouter settings are loaded from environment."""
        with patch.dict(
            "os.environ",
            {
                "OPENROUTER_API_KEY": "or-test",
                "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                "OPENROUTER_ROUTING_MODEL": "openrouter/auto",
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
                "TELEGRAM_BOT_TOKEN": "test",
                "TELEGRAM_WEBHOOK_SECRET": "test",
                "STRIPE_API_KEY": "sk_test",
                "STRIPE_WEBHOOK_SECRET": "whsec_test",
                "STRIPE_PRICE_ID_BASIC": "price_basic",
                "STRIPE_PRICE_ID_PRO": "price_pro",
            },
        ):
            settings = Settings()

            self.assertEqual(settings.OPENROUTER_API_KEY, "or-test")
            self.assertEqual(settings.OPENROUTER_ROUTING_MODEL, "openrouter/auto")
            self.assertEqual(
                settings.OPENROUTER_EMBED_MODEL, "openai/text-embedding-3-small"
            )
            self.assertEqual(settings.OPENROUTER_EMBED_DIMENSIONS, 768)

    def test_required_runtime_config_rejects_placeholders(self):
        """Runtime config validation should fail fast on placeholder values."""
        settings = SimpleNamespace(
            SECRET_KEY="ok",
            DB_NAME="ok",
            MONGO_URI="mongodb://localhost",
            QDRANT_HOST="localhost",
            QDRANT_COLLECTION_NAME="ok",
            QDRANT_API_KEY="ok",
            OPENROUTER_API_KEY="ok",
            OPENROUTER_BASE_URL="ok",
            OPENROUTER_ROUTING_MODEL="ok",
            TELEGRAM_BOT_TOKEN="ok",
            TELEGRAM_WEBHOOK_SECRET="ok",
            STRIPE_API_KEY="ok",
            STRIPE_WEBHOOK_SECRET="ok",
            STRIPE_PRICE_ID_BASIC="ok",
            STRIPE_PRICE_ID_PRO="ok",
        )

        validate_required_runtime_config(settings)

        settings.MONGO_URI = "CHANGE_ME_MONGO_URI"
        with self.assertRaises(ValueError):
            validate_required_runtime_config(settings)


if __name__ == "__main__":
    unittest.main()
