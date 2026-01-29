"""Tests for base repository (common MongoDB operations)."""

import pytest
from unittest.mock import MagicMock, patch
from src.repositories.base import BaseRepository


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def base_repo(mock_db):
    """Create BaseRepository instance with mock database."""
    return BaseRepository(mock_db, "test_collection")


class TestBaseRepositoryInitialization:
    """Test BaseRepository initialization."""

    def test_init_with_valid_collection_name(self, mock_db):
        """Test initialization with valid collection name."""
        repo = BaseRepository(mock_db, "users")
        assert repo.collection is not None
        mock_db.__getitem__.assert_called_once_with("users")

    def test_init_with_different_collection_names(self, mock_db):
        """Test initialization with different collection names."""
        for collection_name in ["users", "chat_history", "workouts", "weights"]:
            mock_db.reset_mock()
            repo = BaseRepository(mock_db, collection_name)
            mock_db.__getitem__.assert_called_once_with(collection_name)

    def test_init_with_special_characters_collection_name(self, mock_db):
        """Test initialization with special characters in collection name."""
        repo = BaseRepository(mock_db, "user_profiles_v2")
        mock_db.__getitem__.assert_called_once_with("user_profiles_v2")

    def test_init_assigns_logger(self, mock_db):
        """Test that logger is assigned during initialization."""
        repo = BaseRepository(mock_db, "test")
        assert hasattr(repo, 'logger')
        assert repo.logger is not None

    def test_collection_property_accessible(self, base_repo):
        """Test that collection is accessible as attribute."""
        assert base_repo.collection is not None


class TestBaseRepositoryCollectionAccess:
    """Test collection access patterns."""

    def test_collection_is_mocked_properly(self, base_repo, mock_db):
        """Test that collection mock works as expected."""
        collection = mock_db.__getitem__.return_value
        base_repo.collection.find_one({"test": "query"})
        collection.find_one.assert_called_once_with({"test": "query"})

    def test_collection_find_operation(self, base_repo, mock_db):
        """Test find operation through collection."""
        mock_db.__getitem__.return_value.find.return_value = []
        result = base_repo.collection.find({})
        assert result == []

    def test_collection_insert_operation(self, base_repo, mock_db):
        """Test insert operation through collection."""
        mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = "123"
        result = base_repo.collection.insert_one({"name": "test"})
        assert result.inserted_id == "123"

    def test_collection_update_operation(self, base_repo, mock_db):
        """Test update operation through collection."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1
        result = base_repo.collection.update_one({"id": "1"}, {"$set": {"name": "updated"}})
        assert result.modified_count == 1

    def test_collection_delete_operation(self, base_repo, mock_db):
        """Test delete operation through collection."""
        mock_db.__getitem__.return_value.delete_one.return_value.deleted_count = 1
        result = base_repo.collection.delete_one({"id": "1"})
        assert result.deleted_count == 1


class TestBaseRepositoryEdgeCases:
    """Test edge cases for base repository."""

    def test_empty_collection_name(self, mock_db):
        """Test initialization with empty collection name."""
        repo = BaseRepository(mock_db, "")
        mock_db.__getitem__.assert_called_once_with("")

    def test_very_long_collection_name(self, mock_db):
        """Test initialization with very long collection name."""
        long_name = "a" * 256
        repo = BaseRepository(mock_db, long_name)
        mock_db.__getitem__.assert_called_once_with(long_name)

    def test_collection_name_with_dots(self, mock_db):
        """Test initialization with collection name containing dots."""
        repo = BaseRepository(mock_db, "db.collection.nested")
        mock_db.__getitem__.assert_called_once_with("db.collection.nested")

    def test_collection_name_with_unicode(self, mock_db):
        """Test initialization with unicode characters in collection name."""
        repo = BaseRepository(mock_db, "usuários_collection")
        mock_db.__getitem__.assert_called_once_with("usuários_collection")

    def test_multiple_repos_same_database(self, mock_db):
        """Test creating multiple repository instances from same database."""
        repo1 = BaseRepository(mock_db, "collection1")
        mock_db.reset_mock()
        repo2 = BaseRepository(mock_db, "collection2")

        # Each should have called __getitem__ once
        assert mock_db.__getitem__.call_count == 1
        mock_db.__getitem__.assert_called_with("collection2")

    def test_multiple_repos_same_collection(self, mock_db):
        """Test creating multiple repository instances with same collection."""
        repo1 = BaseRepository(mock_db, "same_collection")
        repo2 = BaseRepository(mock_db, "same_collection")

        # Both should reference same collection
        assert mock_db.__getitem__.call_count == 2
        mock_db.__getitem__.assert_called_with("same_collection")

    def test_database_connection_error_handling(self, mock_db):
        """Test behavior when database raises error."""
        mock_db.__getitem__.side_effect = Exception("Connection error")

        with pytest.raises(Exception) as exc_info:
            BaseRepository(mock_db, "test")

        assert "Connection error" in str(exc_info.value)

    def test_collection_operations_with_none_filter(self, base_repo, mock_db):
        """Test collection operations with None as filter."""
        collection = mock_db.__getitem__.return_value
        collection.find_one.return_value = None

        result = base_repo.collection.find_one(None)
        assert result is None

    def test_collection_operations_with_empty_dict_filter(self, base_repo, mock_db):
        """Test collection operations with empty dict as filter."""
        collection = mock_db.__getitem__.return_value
        collection.find.return_value.limit.return_value = []

        result = base_repo.collection.find({})
        collection.find.assert_called_once_with({})


class TestBaseRepositoryLogging:
    """Test logging behavior."""

    def test_logger_exists(self, base_repo):
        """Test that logger is available."""
        assert hasattr(base_repo, 'logger')

    def test_logger_has_standard_methods(self, base_repo):
        """Test that logger has standard logging methods."""
        logger = base_repo.logger
        assert callable(getattr(logger, 'debug', None)) or isinstance(logger, MagicMock)
        assert callable(getattr(logger, 'info', None)) or isinstance(logger, MagicMock)
        assert callable(getattr(logger, 'warning', None)) or isinstance(logger, MagicMock)
        assert callable(getattr(logger, 'error', None)) or isinstance(logger, MagicMock)

    def test_logger_consistency(self, mock_db):
        """Test that logger is consistently available across instances."""
        repo1 = BaseRepository(mock_db, "col1")
        repo2 = BaseRepository(mock_db, "col2")

        assert repo1.logger is not None
        assert repo2.logger is not None


class TestBaseRepositoryChaining:
    """Test method chaining and multiple operations."""

    def test_chained_find_operations(self, base_repo, mock_db):
        """Test chained find operations."""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = []

        mock_db.__getitem__.return_value.find.return_value = mock_cursor

        base_repo.collection.find({}).sort("date", -1).limit(10)

        mock_cursor.sort.assert_called_once_with("date", -1)
        mock_cursor.limit.assert_called_once_with(10)

    def test_chained_operations_return_types(self, base_repo, mock_db):
        """Test that chained operations return appropriate types."""
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor

        collection = mock_db.__getitem__.return_value
        collection.find.return_value = mock_cursor

        result = base_repo.collection.find({}).sort("field", 1)
        assert result == mock_cursor
