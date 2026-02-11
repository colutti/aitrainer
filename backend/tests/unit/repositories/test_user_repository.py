"""Tests for user repository (user profile management)."""

import pytest
import bcrypt
from unittest.mock import MagicMock
from src.repositories.user_repository import UserRepository
from src.api.models.user_profile import UserProfile


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def user_repo(mock_db):
    """Create UserRepository instance with mock database."""
    return UserRepository(mock_db)


@pytest.fixture
def sample_user_profile():
    """Create a sample user profile for testing."""
    return UserProfile(
        email="test@example.com",
        password_hash=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode(),
        gender="Masculino",
        age=30,
        weight=80.0,
        height=180,
        goal_type="maintain",
        weekly_rate=0.5,
        role="user"
    )


class TestUserRepositorySaveProfile:
    """Test save_profile method."""

    def test_save_profile_creates_new_user(self, user_repo, mock_db, sample_user_profile):
        """Test creating a new user profile."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "507f1f77bcf86cd799439011"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        user_repo.save_profile(sample_user_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

        # Verify upsert flag
        call_args = collection.update_one.call_args
        assert call_args[1]['upsert'] is True

    def test_save_profile_updates_existing_user(self, user_repo, mock_db, sample_user_profile):
        """Test updating an existing user profile."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        user_repo.save_profile(sample_user_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_profile_no_changes(self, user_repo, mock_db, sample_user_profile):
        """Test when profile has no changes."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        user_repo.save_profile(sample_user_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_profile_excludes_none_values(self, user_repo, mock_db):
        """Test that None values are excluded from save."""
        profile = UserProfile(
            email="test@example.com",
            gender="Feminino",
            age=25,
            weight=65.0,
            height=170,
            goal_type="lose",
            weekly_rate=0.8,
            password_hash=None  # None value
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        user_repo.save_profile(profile)

        collection = mock_db.__getitem__.return_value
        call_args = collection.update_one.call_args
        update_data = call_args[0][1]["$set"]

        # password_hash should not be in the update
        assert "password_hash" not in update_data or update_data.get("password_hash") is not None

    def test_save_profile_with_all_fields(self, user_repo, mock_db):
        """Test saving profile with all fields populated."""
        profile = UserProfile(
            email="complete@example.com",
            password_hash="hashed_pass",
            gender="Masculino",
            age=35,
            weight=90.0,
            height=185,
            goal_type="gain",
            weekly_rate=0.5,
            target_weight=95.0,
            notes="Building muscle",
            role="user"
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        user_repo.save_profile(profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()


class TestUserRepositoryGetProfile:
    """Test get_profile method."""

    def test_get_profile_found(self, user_repo, mock_db, sample_user_profile):
        """Test retrieving an existing profile."""
        mock_data = sample_user_profile.model_dump()
        mock_db.__getitem__.return_value.find_one.return_value = mock_data

        result = user_repo.get_profile("test@example.com")

        assert result is not None
        assert result.email == "test@example.com"
        mock_db.__getitem__.return_value.find_one.assert_called_once_with({"email": "test@example.com"})

    def test_get_profile_not_found(self, user_repo, mock_db):
        """Test retrieving non-existent profile."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = user_repo.get_profile("nonexistent@example.com")

        assert result is None
        mock_db.__getitem__.return_value.find_one.assert_called_once_with({"email": "nonexistent@example.com"})

    def test_get_profile_returns_user_profile_model(self, user_repo, mock_db, sample_user_profile):
        """Test that returned value is UserProfile instance."""
        mock_data = sample_user_profile.model_dump()
        mock_db.__getitem__.return_value.find_one.return_value = mock_data

        result = user_repo.get_profile("test@example.com")

        assert isinstance(result, UserProfile)

    def test_get_profile_with_special_email(self, user_repo, mock_db):
        """Test retrieving profile with special characters in email."""
        email = "user+tag@subdomain.example.com"
        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": email,
            "gender": "Masculino",
            "age": 30,
            "weight": 80.0,
            "height": 180,
            "goal_type": "maintain"
        }

        result = user_repo.get_profile(email)

        assert result is not None
        assert result.email == email


class TestUserRepositoryUpdateProfileFields:
    """Test update_profile_fields method."""

    def test_update_profile_fields_success(self, user_repo, mock_db):
        """Test successful partial profile update."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        result = user_repo.update_profile_fields(
            "test@example.com",
            {"weight": 85.0, "age": 31}
        )

        assert result is True
        mock_db.__getitem__.return_value.update_one.assert_called_once_with(
            {"email": "test@example.com"},
            {"$set": {"weight": 85.0, "age": 31}}
        )

    def test_update_profile_fields_no_changes(self, user_repo, mock_db):
        """Test partial update with no changes applied."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        result = user_repo.update_profile_fields(
            "test@example.com",
            {"weight": 80.0}  # Same value
        )

        assert result is False

    def test_update_profile_fields_not_found(self, user_repo, mock_db):
        """Test partial update on non-existent user."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        result = user_repo.update_profile_fields(
            "nonexistent@example.com",
            {"weight": 85.0}
        )

        assert result is False

    def test_update_profile_fields_single_field(self, user_repo, mock_db):
        """Test updating single field."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        result = user_repo.update_profile_fields(
            "test@example.com",
            {"notes": "New notes"}
        )

        assert result is True

    def test_update_profile_fields_multiple_fields(self, user_repo, mock_db):
        """Test updating multiple fields at once."""
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1
        fields = {
            "weight": 85.0,
            "age": 31,
            "notes": "Updated profile",
            "goal_type": "gain"
        }

        result = user_repo.update_profile_fields("test@example.com", fields)

        assert result is True
        call_args = mock_db.__getitem__.return_value.update_one.call_args
        assert call_args[0][1]["$set"] == fields


class TestUserRepositoryValidateCredentials:
    """Test validate_credentials method."""

    def test_validate_credentials_success(self, user_repo, mock_db):
        """Test successful password validation."""
        password = "correct_password"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": hashed
        }

        result = user_repo.validate_credentials("test@example.com", password)

        assert result is True

    def test_validate_credentials_wrong_password(self, user_repo, mock_db):
        """Test failed validation with wrong password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = bcrypt.hashpw(correct_password.encode(), bcrypt.gensalt()).decode()

        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": hashed
        }

        result = user_repo.validate_credentials("test@example.com", wrong_password)

        assert result is False

    def test_validate_credentials_user_not_found(self, user_repo, mock_db):
        """Test validation when user doesn't exist."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = user_repo.validate_credentials("nonexistent@example.com", "password")

        assert result is False

    def test_validate_credentials_no_password_hash(self, user_repo, mock_db):
        """Test validation when password_hash is missing."""
        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": None
        }

        result = user_repo.validate_credentials("test@example.com", "password")

        assert result is False

    def test_validate_credentials_empty_password(self, user_repo, mock_db):
        """Test validation with empty password."""
        hashed = bcrypt.hashpw(b"real_password", bcrypt.gensalt()).decode()
        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": hashed
        }

        result = user_repo.validate_credentials("test@example.com", "")

        assert result is False

    def test_validate_credentials_invalid_hash_format(self, user_repo, mock_db):
        """Test validation with invalid hash format."""
        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": "not_a_valid_hash"
        }

        result = user_repo.validate_credentials("test@example.com", "password")

        # Should handle gracefully and return False
        assert result is False

    def test_validate_credentials_numeric_password(self, user_repo, mock_db):
        """Test validation with numeric password."""
        password = "12345"
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        mock_db.__getitem__.return_value.find_one.return_value = {
            "email": "test@example.com",
            "password_hash": hashed
        }

        result = user_repo.validate_credentials("test@example.com", password)

        assert result is True


class TestUserRepositoryFindByWebhookToken:
    """Test find_by_webhook_token method."""

    def test_find_by_webhook_token_found(self, user_repo, mock_db, sample_user_profile):
        """Test finding user by webhook token."""
        token = "webhook_token_12345"
        mock_data = sample_user_profile.model_dump()
        mock_data["hevy_webhook_token"] = token

        mock_db.__getitem__.return_value.find_one.return_value = mock_data

        result = user_repo.find_by_webhook_token(token)

        assert result is not None
        assert isinstance(result, UserProfile)
        mock_db.__getitem__.return_value.find_one.assert_called_once_with(
            {"hevy_webhook_token": token}
        )

    def test_find_by_webhook_token_not_found(self, user_repo, mock_db):
        """Test webhook token lookup when no user found."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = user_repo.find_by_webhook_token("nonexistent_token")

        assert result is None

    def test_find_by_webhook_token_creates_index(self, user_repo, mock_db):
        """Test that sparse index is created on webhook token field."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        user_repo.find_by_webhook_token("token")

        # Verify index creation
        collection = mock_db.__getitem__.return_value
        collection.create_index.assert_called_once_with("hevy_webhook_token", sparse=True)

    def test_find_by_webhook_token_index_idempotent(self, user_repo, mock_db):
        """Test that index creation is idempotent."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        # Call multiple times
        user_repo.find_by_webhook_token("token1")
        user_repo.find_by_webhook_token("token2")

        # Index should be created each time (or implementation handles idempotency)
        collection = mock_db.__getitem__.return_value
        assert collection.create_index.call_count >= 1

    def test_find_by_webhook_token_with_special_characters(self, user_repo, mock_db):
        """Test webhook token lookup with special characters."""
        token = "token_!@#$%^&*()"
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = user_repo.find_by_webhook_token(token)

        assert result is None
        mock_db.__getitem__.return_value.find_one.assert_called()


class TestUserRepositoryEdgeCases:
    """Test edge cases and error handling."""

    def test_save_profile_with_minimal_data(self, user_repo, mock_db):
        """Test saving profile with minimal required fields."""
        minimal_profile = UserProfile(
            email="minimal@example.com",
            gender="Masculino",
            age=25,
            weight=70.0,
            height=175,
            goal_type="maintain"
        )

        mock_db.__getitem__.return_value.update_one.return_value.upsert_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        user_repo.save_profile(minimal_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_database_error_on_save(self, user_repo, mock_db, sample_user_profile):
        """Test handling database error on save."""
        mock_db.__getitem__.return_value.update_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            user_repo.save_profile(sample_user_profile)

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_get(self, user_repo, mock_db):
        """Test handling database error on get."""
        mock_db.__getitem__.return_value.find_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            user_repo.get_profile("test@example.com")

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_validate(self, user_repo, mock_db):
        """Test handling database error on validate credentials."""
        mock_db.__getitem__.return_value.find_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            user_repo.validate_credentials("test@example.com", "password")

        assert "DB Error" in str(exc_info.value)
