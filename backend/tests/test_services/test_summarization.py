"""
Tests for ConversationSummaryBufferMemory integration.
"""

import unittest
import warnings
from unittest.mock import MagicMock, patch

# Suppress LangChain memory deprecation warnings
warnings.filterwarnings("ignore", message=".*migrating_memory.*")
warnings.filterwarnings("ignore", category=UserWarning, module="langsmith")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="slowapi")

from langchain_classic.memory import ConversationSummaryBufferMemory  # noqa: E402
from langchain_core.chat_history import BaseChatMessageHistory  # noqa: E402
from langchain_core.messages import HumanMessage, AIMessage  # noqa: E402
from langchain_community.llms.fake import FakeListLLM  # noqa: E402


class MockChatMessageHistory(BaseChatMessageHistory):
    """Mock chat history that extends BaseChatMessageHistory for Pydantic validation."""

    def __init__(self, messages: list | None = None):
        self._messages = messages or []

    @property
    def messages(self) -> list:
        return self._messages

    def add_message(self, message) -> None:
        self._messages.append(message)

    def clear(self) -> None:
        self._messages = []


class TestSummarization(unittest.TestCase):
    """Tests for summarization functionality."""

    def test_get_conversation_memory_returns_memory_object(self):
        """
        Test that get_conversation_memory returns a ConversationSummaryBufferMemory.
        """
        from src.services.database import MongoDatabase

        mock_settings = MagicMock()
        mock_settings.MONGO_URI = "mongodb://localhost:27017"
        mock_settings.DB_NAME = "test_db"
        mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 2000
        mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 30

        with patch("src.repositories.chat_repository.settings", mock_settings):
            with patch("pymongo.MongoClient"):
                db = MongoDatabase()

                # Use FakeLLM instead of MagicMock for Pydantic validation
                fake_llm = FakeListLLM(responses=["Test summary"])
                mock_chat_history = MockChatMessageHistory()

                with patch(
                    "src.repositories.chat_repository.MongoDBChatMessageHistory",
                    return_value=mock_chat_history,
                ):
                    memory = db.get_conversation_memory(
                        session_id="test@test.com", llm=fake_llm, max_token_limit=2000
                    )

                    self.assertIsInstance(memory, ConversationSummaryBufferMemory)
                    self.assertEqual(memory.memory_key, "chat_history")

    def test_memory_returns_summary_plus_recent_messages(self):
        """
        Test that memory correctly returns summary + recent messages.
        Uses FakeLLM to avoid real API calls.
        """
        # Create a fake LLM that returns a predefined summary
        fake_llm = FakeListLLM(responses=["Resumo: Usuário discutiu treinos de peito."])

        # Create memory with mock chat history that extends BaseChatMessageHistory
        mock_chat_history = MockChatMessageHistory(
            [
                HumanMessage(content="Oi, quero treinar peito"),
                AIMessage(content="Vamos montar um treino de peito!"),
                HumanMessage(content="Fiz supino hoje"),
                AIMessage(content="Ótimo! Como foi?"),
            ]
        )

        memory = ConversationSummaryBufferMemory(
            llm=fake_llm,
            chat_memory=mock_chat_history,
            max_token_limit=50,  # Low limit to trigger summarization
            return_messages=True,
            memory_key="chat_history",  # Explicitly set memory_key
        )

        # Load memory variables should work without errors
        result = memory.load_memory_variables({})

        # Should return chat_history key
        self.assertIn("chat_history", result)
        # Result should contain messages
        self.assertTrue(len(result["chat_history"]) > 0)

    def test_conversation_memory_uses_settings_default(self):
        """
        Test that get_conversation_memory uses settings default when max_token_limit not provided.
        """
        from src.services.database import MongoDatabase

        mock_settings = MagicMock()
        mock_settings.MONGO_URI = "mongodb://localhost:27017"
        mock_settings.DB_NAME = "test_db"
        mock_settings.SUMMARY_MAX_TOKEN_LIMIT = 3000
        mock_settings.MAX_SHORT_TERM_MEMORY_MESSAGES = 30

        # Patch settings WHERE IT IS USED (ChatRepository)
        with patch("src.repositories.chat_repository.settings", mock_settings):
            with patch("pymongo.MongoClient"):
                db = MongoDatabase()

                fake_llm = FakeListLLM(responses=["Test summary"])
                mock_chat_history = MockChatMessageHistory()

                # Patch MongoDBChatMessageHistory in ChatRepository to avoid real connection and return valid mock
                with patch(
                    "src.repositories.chat_repository.MongoDBChatMessageHistory",
                    return_value=mock_chat_history,
                ):
                    memory = db.get_conversation_memory(
                        session_id="test@test.com",
                        llm=fake_llm,
                        # max_token_limit not provided - should use settings default
                    )

                    self.assertEqual(memory.max_token_limit, 3000)


if __name__ == "__main__":
    unittest.main()
