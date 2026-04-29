"""Unit tests for LangSmith helper module."""

import unittest
from unittest.mock import patch, MagicMock

from src.core import langsmith


class TestLangSmith(unittest.TestCase):
    @patch("src.core.langsmith.settings")
    def test_is_tracing_enabled_false_when_disabled(self, mock_settings):
        mock_settings.LANGSMITH_TRACING = False
        mock_settings.LANGSMITH_TRACING_ENABLED = False
        mock_settings.LANGSMITH_API_KEY = "key"
        mock_settings.LANGSMITH_PROJECT = "proj"
        self.assertFalse(langsmith.is_tracing_enabled())

    @patch("src.core.langsmith.settings")
    def test_is_tracing_enabled_false_without_key(self, mock_settings):
        mock_settings.LANGSMITH_TRACING = True
        mock_settings.LANGSMITH_TRACING_ENABLED = True
        mock_settings.LANGSMITH_API_KEY = ""
        mock_settings.LANGSMITH_PROJECT = "proj"
        self.assertFalse(langsmith.is_tracing_enabled())

    @patch("src.core.langsmith.settings")
    def test_build_runnable_config_noop_when_disabled(self, mock_settings):
        mock_settings.LANGSMITH_TRACING = False
        mock_settings.LANGSMITH_TRACING_ENABLED = False
        config = langsmith.build_runnable_config(
            run_name="chat.simple",
            mode="simple",
            user_email="a@b.com",
            input_data={},
        )
        self.assertEqual(config, {})

    @patch("src.core.langsmith.settings")
    def test_build_runnable_config_with_defaults(self, mock_settings):
        mock_settings.LANGSMITH_TRACING = True
        mock_settings.LANGSMITH_TRACING_ENABLED = True
        mock_settings.LANGSMITH_API_KEY = "k"
        mock_settings.LANGSMITH_PROJECT = "p"
        mock_settings.LANGSMITH_ENVIRONMENT = "dev"
        config = langsmith.build_runnable_config(
            run_name="chat.tools",
            mode="tools",
            user_email="a@b.com",
            input_data={"user_message": "hello", "tools": ["x"]},
            recursion_limit=12,
        )
        self.assertEqual(config["run_name"], "chat.tools")
        self.assertEqual(config["recursion_limit"], 12)
        self.assertIn("env:dev", config["tags"])
        self.assertEqual(config["metadata"]["session_id"], "a@b.com")

    @patch("src.core.langsmith._build_callbacks")
    @patch("src.core.langsmith.settings")
    def test_build_runnable_config_includes_callbacks(self, mock_settings, mock_callbacks):
        mock_settings.LANGSMITH_TRACING = True
        mock_settings.LANGSMITH_TRACING_ENABLED = True
        mock_settings.LANGSMITH_API_KEY = "k"
        mock_settings.LANGSMITH_PROJECT = "p"
        mock_settings.LANGSMITH_ENVIRONMENT = "dev"
        mock_callbacks.return_value = ["tracer"]
        config = langsmith.build_runnable_config(
            run_name="chat.tools",
            mode="tools",
            user_email="a@b.com",
            input_data={"user_message": "hello"},
        )
        self.assertEqual(config["callbacks"], ["tracer"])

    @patch("langsmith.run_helpers.get_current_run_tree")
    def test_create_tool_run_span(self, mock_get_current_run_tree):
        mock_tree = MagicMock()
        mock_child = MagicMock()
        mock_tree.create_child.return_value = mock_child
        mock_get_current_run_tree.return_value = mock_tree
        langsmith.create_tool_run_span("list_events", "ok", "call-1")
        mock_tree.create_child.assert_called_once()
        mock_child.end.assert_called_once()


if __name__ == "__main__":
    unittest.main()
