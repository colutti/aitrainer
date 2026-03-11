"""Tests for Telegram repository (critical paths)."""

import pytest
import string
from unittest.mock import MagicMock
from src.repositories.telegram_repository import TelegramRepository


@pytest.fixture
def mock_db():
    db_mock = MagicMock()
    db_mock["telegram_links"] = MagicMock()
    db_mock["telegram_codes"] = MagicMock()
    return db_mock


@pytest.fixture
def telegram_repo(mock_db):
    return TelegramRepository(mock_db)


class TestLinkingCode:
    """Test critical linking code scenarios."""

    def test_create_code_generates_valid_string(self, telegram_repo):
        """Test code is 6 alphanumeric characters."""
        code = telegram_repo.create_linking_code("user@test.com")
        assert len(code) == 6
        assert all(c in string.ascii_uppercase + string.digits for c in code)

    def test_validate_code_returns_email_on_success(self, telegram_repo, mock_db):
        """Test successful validation returns email."""
        mock_db["telegram_codes"].find_one_and_delete.return_value = {
            "user_email": "user@test.com"
        }
        result = telegram_repo.validate_and_consume_code("ABC123", 123456789)
        assert result == "user@test.com"

    def test_validate_code_returns_none_on_invalid(self, telegram_repo, mock_db):
        """Test invalid code returns None."""
        mock_db["telegram_codes"].find_one_and_delete.return_value = None
        result = telegram_repo.validate_and_consume_code("INVALID", 123456789)
        assert result is None

    def test_get_link_by_chat_id_not_found(self, telegram_repo, mock_db):
        """Test retrieving non-existent link."""
        mock_db["telegram_links"].find_one.return_value = None
        result = telegram_repo.get_link_by_chat_id(999999999)
        assert result is None

    def test_delete_link_success(self, telegram_repo, mock_db):
        """Test delete returns True on success."""
        mock_result = MagicMock()
        mock_result.deleted_count = 1
        mock_db["telegram_links"].delete_one.return_value = mock_result
        result = telegram_repo.delete_link("user@test.com")
        assert result is True

    def test_delete_link_not_found(self, telegram_repo, mock_db):
        """Test delete returns False when not found."""
        mock_result = MagicMock()
        mock_result.deleted_count = 0
        mock_db["telegram_links"].delete_one.return_value = mock_result
        result = telegram_repo.delete_link("nonexistent@test.com")
        assert result is False

class TestIdempotency:
    """Test message idempotency tracking."""

    def test_try_record_update_success(self, telegram_repo, mock_db):
        """Test recording a new update_id returns True."""
        mock_db["telegram_processed_updates"].insert_one.return_value = MagicMock()
        result = telegram_repo.try_record_update(123)
        assert result is True
        mock_db["telegram_processed_updates"].insert_one.assert_called_once()

    def test_try_record_update_duplicate_fails(self, telegram_repo, mock_db):
        """Test recording a duplicate update_id returns False."""
        # Use a real exception to simulate duplicate key error
        mock_db["telegram_processed_updates"].insert_one.side_effect = Exception("Duplicate key")
        result = telegram_repo.try_record_update(123)
        assert result is False
