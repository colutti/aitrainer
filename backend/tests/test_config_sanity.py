import unittest
from src.core.config import settings


class TestConfigBug(unittest.TestCase):
    def test_openai_model_name_integrity(self):
        """
        Reproduce environment variable concatenation bug.
        The model name should not be polluted with other configuration keys.
        """
        print(f"Current OPENAI_MODEL_NAME: {settings.OPENAI_MODEL_NAME}")

        # Check for concatenation artifacts
        self.assertNotIn(
            "SUMMARY_MAX_TOKEN_LIMIT",
            settings.OPENAI_MODEL_NAME,
            "BUG DETECTED: OPENAI_MODEL_NAME is concatenated with SUMMARY_MAX_TOKEN_LIMIT",
        )

        # Check for valid model ID (basic validation)
        valid_models = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-4-turbo",
            "gpt-5-mini",
        ]
        self.assertIn(
            settings.OPENAI_MODEL_NAME,
            valid_models,
            f"Invalid model ID: {settings.OPENAI_MODEL_NAME}. Expected one of {valid_models}",
        )
