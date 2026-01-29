"""Tests for chat repository (chat history management)."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, Mock
from src.repositories.chat_repository import ChatRepository
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def chat_repo(mock_db):
    """Create ChatRepository instance with mock database."""
    return ChatRepository(mock_db)


@pytest.fixture
def sample_chat_history():
    """Create sample chat history for testing."""
    return ChatHistory(
        text="Hello trainer!",
        sender=Sender.STUDENT,
        timestamp=datetime.now().isoformat(),
        trainer_type="atlas"
    )


@pytest.fixture
def mock_llm():
    """Create mock LLM for testing."""
    return MagicMock()


class TestChatRepositoryGetHistory:
    """Test get_history method."""

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ChatHistory')
    def test_get_history_default_limit(self, mock_chat_history_class, mock_mongo_history, chat_repo):
        """Test retrieving chat history with default limit."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance
        mock_chat_history_class.from_mongodb_chat_message_history.return_value = []

        result = chat_repo.get_history("user_123")

        mock_mongo_history.assert_called_once()
        mock_chat_history_class.from_mongodb_chat_message_history.assert_called_once_with(mock_mongo_instance)

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ChatHistory')
    def test_get_history_custom_limit(self, mock_chat_history_class, mock_mongo_history, chat_repo):
        """Test retrieving chat history with custom limit."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance
        mock_chat_history_class.from_mongodb_chat_message_history.return_value = []

        result = chat_repo.get_history("user_123", limit=50)

        # Verify MongoDBChatMessageHistory was initialized with correct history_size
        call_kwargs = mock_mongo_history.call_args[1]
        assert call_kwargs['history_size'] == 50

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ChatHistory')
    def test_get_history_returns_chat_history_list(self, mock_chat_history_class, mock_mongo_history, chat_repo):
        """Test that get_history returns list of ChatHistory objects."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        expected_histories = [
            ChatHistory(
                text="Hello",
                sender=Sender.STUDENT,
                timestamp=datetime.now().isoformat()
            )
        ]
        mock_chat_history_class.from_mongodb_chat_message_history.return_value = expected_histories

        result = chat_repo.get_history("user_123")

        assert isinstance(result, list)


class TestChatRepositoryAddMessage:
    """Test add_message method."""

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.HumanMessage')
    @patch('src.repositories.chat_repository.AIMessage')
    def test_add_message_from_student(self, mock_ai_msg, mock_human_msg, mock_mongo_history, chat_repo):
        """Test adding a student message."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="I want to train",
            sender=Sender.STUDENT,
            timestamp=datetime.now().isoformat()
        )

        chat_repo.add_message(chat_msg, "session_123")

        # Should call HumanMessage
        mock_human_msg.assert_called_once()
        call_args = mock_human_msg.call_args
        assert "I want to train" in str(call_args)

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.HumanMessage')
    @patch('src.repositories.chat_repository.AIMessage')
    def test_add_message_from_trainer(self, mock_ai_msg, mock_human_msg, mock_mongo_history, chat_repo):
        """Test adding a trainer message."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="Great! Let's start training.",
            sender=Sender.TRAINER,
            timestamp=datetime.now().isoformat()
        )

        chat_repo.add_message(chat_msg, "session_123")

        # Should call AIMessage
        mock_ai_msg.assert_called_once()
        call_args = mock_ai_msg.call_args
        assert "Great!" in str(call_args)

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.HumanMessage')
    @patch('src.repositories.chat_repository.AIMessage')
    def test_add_message_with_trainer_type(self, mock_ai_msg, mock_human_msg, mock_mongo_history, chat_repo):
        """Test adding message with trainer type."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="Message",
            sender=Sender.TRAINER,
            timestamp=datetime.now().isoformat()
        )

        chat_repo.add_message(chat_msg, "session_123", trainer_type="luna")

        # Verify AIMessage called with trainer_type in additional_kwargs
        mock_ai_msg.assert_called_once()
        call_kwargs = mock_ai_msg.call_args[1]
        assert call_kwargs['additional_kwargs']['trainer_type'] == "luna"

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.HumanMessage')
    def test_add_message_includes_timestamp(self, mock_human_msg, mock_mongo_history, chat_repo):
        """Test that added messages include timestamp."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        now = datetime.now()
        chat_msg = ChatHistory(
            text="Message",
            sender=Sender.STUDENT,
            timestamp=now.isoformat()
        )

        chat_repo.add_message(chat_msg, "session_123")

        mock_human_msg.assert_called_once()
        call_kwargs = mock_human_msg.call_args[1]
        assert 'additional_kwargs' in call_kwargs
        assert 'timestamp' in call_kwargs['additional_kwargs']

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.AIMessage')
    def test_add_message_without_trainer_type(self, mock_ai_msg, mock_mongo_history, chat_repo):
        """Test adding message without specifying trainer_type."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="Message",
            sender=Sender.TRAINER,
            timestamp=datetime.now().isoformat()
        )

        chat_repo.add_message(chat_msg, "session_123", trainer_type=None)

        mock_ai_msg.assert_called_once()
        call_kwargs = mock_ai_msg.call_args[1]
        # trainer_type should not be in additional_kwargs
        assert 'trainer_type' not in call_kwargs.get('additional_kwargs', {})


class TestChatRepositoryGetMemoryBuffer:
    """Test get_memory_buffer method."""

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationSummaryBufferMemory')
    def test_get_memory_buffer_default_token_limit(self, mock_memory_class, mock_mongo_history, chat_repo, mock_llm):
        """Test getting memory buffer with default token limit."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_repo.get_memory_buffer("session_123", mock_llm)

        # Verify ConversationSummaryBufferMemory was created
        mock_memory_class.assert_called_once()

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationSummaryBufferMemory')
    def test_get_memory_buffer_custom_token_limit(self, mock_memory_class, mock_mongo_history, chat_repo, mock_llm):
        """Test getting memory buffer with custom token limit."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_repo.get_memory_buffer("session_123", mock_llm, max_token_limit=2000)

        # Verify token limit was passed
        mock_memory_class.assert_called_once()
        call_kwargs = mock_memory_class.call_args[1]
        assert call_kwargs['max_token_limit'] == 2000

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationSummaryBufferMemory')
    def test_get_memory_buffer_with_llm(self, mock_memory_class, mock_mongo_history, chat_repo, mock_llm):
        """Test memory buffer receives correct LLM."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_repo.get_memory_buffer("session_123", mock_llm)

        mock_memory_class.assert_called_once()
        call_kwargs = mock_memory_class.call_args[1]
        assert call_kwargs['llm'] == mock_llm


class TestChatRepositoryGetWindowMemory:
    """Test get_window_memory method."""

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationBufferWindowMemory')
    def test_get_window_memory_default_k(self, mock_window_memory_class, mock_mongo_history, chat_repo):
        """Test getting window memory with default k."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_repo.get_window_memory("session_123")

        mock_window_memory_class.assert_called_once()
        call_kwargs = mock_window_memory_class.call_args[1]
        assert call_kwargs['k'] == 40

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationBufferWindowMemory')
    def test_get_window_memory_custom_k(self, mock_window_memory_class, mock_mongo_history, chat_repo):
        """Test getting window memory with custom k."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_repo.get_window_memory("session_123", k=20)

        mock_window_memory_class.assert_called_once()
        call_kwargs = mock_window_memory_class.call_args[1]
        assert call_kwargs['k'] == 20

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    @patch('src.repositories.chat_repository.ConversationBufferWindowMemory')
    def test_get_window_memory_returns_memory_object(self, mock_window_memory_class, mock_mongo_history, chat_repo):
        """Test that window memory returns memory object."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance
        mock_memory_instance = MagicMock()
        mock_window_memory_class.return_value = mock_memory_instance

        result = chat_repo.get_window_memory("session_123")

        assert result == mock_memory_instance


class TestChatRepositoryGetUnsummarizedMessages:
    """Test get_unsummarized_messages method."""

    def test_get_unsummarized_messages_returns_empty_list(self, chat_repo):
        """Test that get_unsummarized_messages returns empty list."""
        result = chat_repo.get_unsummarized_messages("session_123")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_unsummarized_messages_custom_skip_last(self, chat_repo):
        """Test get_unsummarized_messages with custom skip_last."""
        result = chat_repo.get_unsummarized_messages("session_123", skip_last=50)

        assert isinstance(result, list)

    def test_get_unsummarized_messages_placeholder_behavior(self, chat_repo):
        """Test placeholder behavior is documented."""
        # This is a placeholder method that returns empty list
        # Used for future implementation of message compaction
        result = chat_repo.get_unsummarized_messages("any_session")

        # Should return empty list until full implementation
        assert result == []


class TestChatRepositoryInitialization:
    """Test ChatRepository initialization."""

    def test_chat_repository_inherits_from_base(self, chat_repo):
        """Test that ChatRepository inherits from BaseRepository."""
        assert hasattr(chat_repo, 'collection')
        assert hasattr(chat_repo, 'logger')

    def test_chat_repository_collection_name(self, mock_db):
        """Test that ChatRepository uses correct collection name."""
        repo = ChatRepository(mock_db)
        mock_db.__getitem__.assert_called_once_with("chat_history")

    def test_chat_repository_with_mock_database(self, mock_db):
        """Test ChatRepository initialization with mock database."""
        repo = ChatRepository(mock_db)
        assert repo is not None


class TestChatRepositoryEdgeCases:
    """Test edge cases and error handling."""

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    def test_get_history_empty_session(self, mock_mongo_history, chat_repo):
        """Test getting history for empty session."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        with patch('src.repositories.chat_repository.ChatHistory') as mock_chat_cls:
            mock_chat_cls.from_mongodb_chat_message_history.return_value = []

            result = chat_repo.get_history("")

            assert isinstance(result, list)

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    def test_add_message_empty_text(self, mock_mongo_history, chat_repo):
        """Test adding message with empty text."""
        mock_mongo_instance = MagicMock()
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="",
            sender=Sender.STUDENT,
            timestamp=datetime.now().isoformat()
        )

        with patch('src.repositories.chat_repository.HumanMessage') as mock_human:
            chat_repo.add_message(chat_msg, "session_123")
            mock_human.assert_called_once()

    @patch('src.repositories.chat_repository.MongoDBChatMessageHistory')
    def test_database_error_on_add_message(self, mock_mongo_history, chat_repo):
        """Test handling database error on add_message."""
        mock_mongo_instance = MagicMock()
        mock_mongo_instance.add_message.side_effect = Exception("DB Error")
        mock_mongo_history.return_value = mock_mongo_instance

        chat_msg = ChatHistory(
            text="Message",
            sender=Sender.STUDENT,
            timestamp=datetime.now().isoformat()
        )

        with patch('src.repositories.chat_repository.HumanMessage'):
            with pytest.raises(Exception) as exc_info:
                chat_repo.add_message(chat_msg, "session_123")

            assert "DB Error" in str(exc_info.value)
