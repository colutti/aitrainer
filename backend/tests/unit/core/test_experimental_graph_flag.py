"""Tests for conversation graph rollout flag defaults."""

from src.core.config import settings


def test_experimental_conversation_graph_enabled_by_default():
    assert settings.ENABLE_EXPERIMENTAL_CONVERSATION_GRAPH is True
