"""
Tests for InviteRepository.
"""

from datetime import datetime, timedelta, timezone
import uuid
import pytest
from unittest.mock import MagicMock, patch
from src.api.models.invite import Invite
from src.repositories.invite_repository import InviteRepository


@pytest.fixture
def mock_database():
    """Fixture for mocked MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def invite_repo(mock_database):
    """Fixture for InviteRepository with mocked database."""
    with patch.object(InviteRepository, "_ensure_indexes"):
        repo = InviteRepository(mock_database)
        return repo


@pytest.fixture
def sample_invite():
    """Fixture for a sample invite."""
    return Invite(
        token=str(uuid.uuid4()),
        email="test@example.com",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        used=False,
        used_at=None,
    )


def test_create_invite(invite_repo, sample_invite):
    """Test creating a new invite."""
    invite_repo.create(sample_invite)

    invite_repo.collection.insert_one.assert_called_once_with(
        sample_invite.model_dump()
    )


def test_get_by_token_found(invite_repo, sample_invite):
    """Test retrieving invite by token."""
    invite_repo.collection.find_one.return_value = sample_invite.model_dump()

    result = invite_repo.get_by_token(sample_invite.token)

    assert result is not None
    assert result.email == sample_invite.email
    assert result.token == sample_invite.token


def test_get_by_token_not_found(invite_repo):
    """Test retrieving non-existent invite returns None."""
    invite_repo.collection.find_one.return_value = None

    result = invite_repo.get_by_token("nonexistent-token")

    assert result is None


def test_get_by_email(invite_repo):
    """Test retrieving invite by email."""
    invite_data = {
        "token": str(uuid.uuid4()),
        "email": "user@test.com",
        "created_at": datetime.now(timezone.utc),
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=72),
        "used": False,
        "used_at": None,
    }
    invite_repo.collection.find_one.return_value = invite_data

    result = invite_repo.get_by_email("user@test.com")

    assert result is not None
    assert result.email == "user@test.com"
    invite_repo.collection.find_one.assert_called_once_with(
        {"email": "user@test.com"}, sort=[("created_at", -1)]
    )


def test_mark_as_used_success(invite_repo, sample_invite):
    """Test marking invite as used."""
    mock_result = MagicMock()
    mock_result.modified_count = 1
    invite_repo.collection.update_one.return_value = mock_result

    result = invite_repo.mark_as_used(sample_invite.token)

    assert result is True
    invite_repo.collection.update_one.assert_called_once()


def test_mark_as_used_not_found(invite_repo):
    """Test marking non-existent invite as used."""
    mock_result = MagicMock()
    mock_result.modified_count = 0
    invite_repo.collection.update_one.return_value = mock_result

    result = invite_repo.mark_as_used("nonexistent-token")

    assert result is False


def test_revoke_success(invite_repo, sample_invite):
    """Test revoking an invite."""
    mock_result = MagicMock()
    mock_result.deleted_count = 1
    invite_repo.collection.delete_one.return_value = mock_result

    result = invite_repo.revoke(sample_invite.token)

    assert result is True
    invite_repo.collection.delete_one.assert_called_once_with(
        {"token": sample_invite.token}
    )


def test_revoke_not_found(invite_repo):
    """Test revoking non-existent invite."""
    mock_result = MagicMock()
    mock_result.deleted_count = 0
    invite_repo.collection.delete_one.return_value = mock_result

    result = invite_repo.revoke("nonexistent-token")

    assert result is False


def test_list_active(invite_repo):
    """Test listing active invites."""
    now = datetime.now(timezone.utc)
    active_invite_data = {
        "token": str(uuid.uuid4()),
        "email": "active@test.com",
        "created_at": now,
        "expires_at": now + timedelta(hours=72),
        "used": False,
        "used_at": None,
    }

    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = [active_invite_data]
    invite_repo.collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    active_invites = invite_repo.list_active()

    assert len(active_invites) == 1
    assert active_invites[0].email == "active@test.com"


def test_has_active_invite_true(invite_repo):
    """Test checking for active invite by email - exists."""
    invite_repo.collection.count_documents.return_value = 1

    result = invite_repo.has_active_invite("active@test.com")

    assert result is True


def test_has_active_invite_false(invite_repo):
    """Test checking for active invite by email - does not exist."""
    invite_repo.collection.count_documents.return_value = 0

    result = invite_repo.has_active_invite("none@test.com")

    assert result is False
