"""
Tests for AI provider switching logic (Gemini vs Ollama).
"""

import unittest
from unittest.mock import patch

from src.core.config import Settings


class TestAIProviderSwitching(unittest.TestCase):
    """
    Test suite for environment-based AI provider selection.
    """

    def test_get_mem0_config_gemini(self):
        """
        Verify Mem0 configuration for Gemini provider.
        """
        with patch.dict(
            "os.environ",
            {
                "AI_PROVIDER": "gemini",
                "GEMINI_API_KEY": "test_key",
                "GEMINI_LLM_MODEL": "test_llm",
                "GEMINI_EMBEDDER_MODEL": "test_embed",
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
            config = settings.get_mem0_config()

            self.assertEqual(config["llm"]["provider"], "gemini")
            self.assertEqual(config["llm"]["config"]["model"], "test_llm")
            self.assertEqual(config["llm"]["config"]["api_key"], "test_key")

            self.assertEqual(config["embedder"]["provider"], "gemini")
            self.assertEqual(config["embedder"]["config"]["model"], "test_embed")
            self.assertEqual(config["embedder"]["config"]["api_key"], "test_key")

    def test_get_mem0_config_ollama(self):
        """
        Verify Mem0 configuration for Ollama provider.
        """
        with patch.dict(
            "os.environ",
            {
                "AI_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "http://ollama-host:11434",
                "OLLAMA_LLM_MODEL": "llama-test",
                "OLLAMA_EMBEDDER_MODEL": "embed-test",
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
            config = settings.get_mem0_config()

            self.assertEqual(config["llm"]["provider"], "ollama")
            self.assertEqual(config["llm"]["config"]["model"], "llama-test")
            self.assertEqual(
                config["llm"]["config"]["ollama_base_url"], "http://ollama-host:11434"
            )

            self.assertEqual(config["embedder"]["provider"], "ollama")
            self.assertEqual(config["embedder"]["config"]["model"], "embed-test")
            self.assertEqual(
                config["embedder"]["config"]["ollama_base_url"],
                "http://ollama-host:11434",
            )


if __name__ == "__main__":
    unittest.main()
