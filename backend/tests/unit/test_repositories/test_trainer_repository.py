"""Tests for trainer repository (trainer profile management)."""

import pytest
from unittest.mock import MagicMock
from src.repositories.trainer_repository import TrainerRepository
from src.api.models.trainer_profile import TrainerProfile


@pytest.fixture
def mock_db():
    """Create mock MongoDB database."""
    db_mock = MagicMock()
    collection_mock = MagicMock()
    db_mock.__getitem__.return_value = collection_mock
    return db_mock


@pytest.fixture
def trainer_repo(mock_db):
    """Create TrainerRepository instance with mock database."""
    return TrainerRepository(mock_db)


@pytest.fixture
def sample_trainer_profile():
    """Create a sample trainer profile for testing."""
    return TrainerProfile(
        user_email="user@example.com",
        trainer_type="atlas"
    )


class TestTrainerRepositoryInitialization:
    """Test TrainerRepository initialization."""

    def test_trainer_repository_collection_name(self, mock_db):
        """Test that TrainerRepository uses correct collection name."""
        _ = TrainerRepository(mock_db)
        mock_db.__getitem__.assert_called_once_with("trainer_profiles")

    def test_trainer_repository_inherits_from_base(self, trainer_repo):
        """Test that TrainerRepository inherits from BaseRepository."""
        assert hasattr(trainer_repo, 'collection')
        assert hasattr(trainer_repo, 'logger')

    def test_trainer_repository_with_mock_database(self, mock_db):
        """Test TrainerRepository initialization with mock database."""
        repo = TrainerRepository(mock_db)
        assert repo is not None


class TestTrainerRepositorySaveProfile:
    """Test save_profile method."""

    def test_save_profile_creates_new_profile(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test creating a new trainer profile."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "507f1f77bcf86cd799439011"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(sample_trainer_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

        # Verify upsert flag
        call_args = collection.update_one.call_args
        assert call_args[1]['upsert'] is True

    def test_save_profile_updates_existing_profile(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test updating an existing trainer profile."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        trainer_repo.save_profile(sample_trainer_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_profile_no_changes(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test when profile has no changes."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(sample_trainer_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_save_profile_uses_email_as_key(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test that email is used as query key."""
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(sample_trainer_profile)

        collection = mock_db.__getitem__.return_value
        call_args = collection.update_one.call_args
        filter_doc = call_args[0][0]

        assert filter_doc == {"user_email": "user@example.com"}

    def test_save_profile_sets_trainer_type(self, trainer_repo, mock_db):
        """Test that trainer type is set correctly."""
        profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="luna"
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(profile)

        collection = mock_db.__getitem__.return_value
        call_args = collection.update_one.call_args
        update_doc = call_args[0][1]

        assert update_doc["$set"]["trainer_type"] == "luna"

    def test_save_profile_with_different_trainers(self, trainer_repo, mock_db):
        """Test saving profiles with different trainer types."""
        trainer_types = ["atlas", "luna", "sofia", "sargento", "gymbro"]

        for trainer_type in trainer_types:
            mock_db.__getitem__.return_value.reset_mock()
            mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
            mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

            profile = TrainerProfile(
                user_email="user@example.com",
                trainer_type=trainer_type
            )

            trainer_repo.save_profile(profile)

            collection = mock_db.__getitem__.return_value
            call_args = collection.update_one.call_args
            update_doc = call_args[0][1]

            assert update_doc["$set"]["trainer_type"] == trainer_type

    def test_save_profile_multiple_updates(self, trainer_repo, mock_db):
        """Test updating same profile multiple times."""
        profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="atlas"
        )

        # First save
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0
        trainer_repo.save_profile(profile)

        # Update with different trainer
        mock_db.__getitem__.return_value.reset_mock()
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        profile2 = TrainerProfile(
            user_email="user@example.com",
            trainer_type="luna"
        )
        trainer_repo.save_profile(profile2)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()


class TestTrainerRepositoryGetProfile:
    """Test get_profile method."""

    def test_get_profile_found(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test retrieving an existing profile."""
        mock_data = sample_trainer_profile.model_dump()
        mock_db.__getitem__.return_value.find_one.return_value = mock_data

        result = trainer_repo.get_profile("user@example.com")

        assert result is not None
        assert result.user_email == "user@example.com"
        assert result.trainer_type == "atlas"
        mock_db.__getitem__.return_value.find_one.assert_called_once_with(
            {"user_email": "user@example.com"}
        )

    def test_get_profile_not_found(self, trainer_repo, mock_db):
        """Test retrieving non-existent profile."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = trainer_repo.get_profile("nonexistent@example.com")

        assert result is None
        mock_db.__getitem__.return_value.find_one.assert_called_once_with(
            {"user_email": "nonexistent@example.com"}
        )

    def test_get_profile_returns_trainer_profile_model(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test that returned value is TrainerProfile instance."""
        mock_data = sample_trainer_profile.model_dump()
        mock_db.__getitem__.return_value.find_one.return_value = mock_data

        result = trainer_repo.get_profile("user@example.com")

        assert isinstance(result, TrainerProfile)

    def test_get_profile_with_different_trainers(self, trainer_repo, mock_db):
        """Test retrieving profiles with different trainer types."""
        trainer_types = ["atlas", "luna", "sofia", "sargento", "gymbro"]

        for trainer_type in trainer_types:
            mock_db.__getitem__.return_value.reset_mock()
            mock_data = {
                "user_email": "user@example.com",
                "trainer_type": trainer_type
            }
            mock_db.__getitem__.return_value.find_one.return_value = mock_data

            result = trainer_repo.get_profile("user@example.com")

            assert result is not None
            assert result.trainer_type == trainer_type

    def test_get_profile_with_special_email(self, trainer_repo, mock_db):
        """Test retrieving profile with special characters in email."""
        email = "user+tag@subdomain.example.com"
        mock_db.__getitem__.return_value.find_one.return_value = {
            "user_email": email,
            "trainer_type": "atlas"
        }

        result = trainer_repo.get_profile(email)

        assert result is not None
        assert result.user_email == email


class TestTrainerRepositoryProfileSwitching:
    """Test trainer profile switching scenarios."""

    def test_switch_trainer_for_existing_user(self, trainer_repo, mock_db):
        """Test switching trainer for user with existing profile."""
        # First, get existing profile
        mock_db.__getitem__.return_value.find_one.return_value = {
            "user_email": "user@example.com",
            "trainer_type": "atlas"
        }

        result = trainer_repo.get_profile("user@example.com")
        assert result.trainer_type == "atlas"

        # Update to new trainer
        mock_db.__getitem__.return_value.reset_mock()
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        new_profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="luna"
        )
        trainer_repo.save_profile(new_profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_profile_persistence_across_calls(self, trainer_repo, mock_db):
        """Test that profile data persists correctly."""
        profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="sofia"
        )

        # Save
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(profile)

        # Retrieve
        mock_db.__getitem__.return_value.reset_mock()
        mock_db.__getitem__.return_value.find_one.return_value = profile.model_dump()

        result = trainer_repo.get_profile("user@example.com")

        assert result.trainer_type == "sofia"


class TestTrainerRepositoryEdgeCases:
    """Test edge cases and error handling."""

    def test_save_profile_with_minimal_data(self, trainer_repo, mock_db):
        """Test saving profile with only required fields."""
        profile = TrainerProfile(
            user_email="minimal@example.com",
            trainer_type="atlas"
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

        trainer_repo.save_profile(profile)

        collection = mock_db.__getitem__.return_value
        collection.update_one.assert_called_once()

    def test_get_profile_with_empty_email(self, trainer_repo, mock_db):
        """Test retrieving profile with empty email."""
        mock_db.__getitem__.return_value.find_one.return_value = None

        result = trainer_repo.get_profile("")

        assert result is None

    def test_database_error_on_save(self, trainer_repo, mock_db, sample_trainer_profile):
        """Test handling database error on save."""
        mock_db.__getitem__.return_value.update_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            trainer_repo.save_profile(sample_trainer_profile)

        assert "DB Error" in str(exc_info.value)

    def test_database_error_on_get(self, trainer_repo, mock_db):
        """Test handling database error on get."""
        mock_db.__getitem__.return_value.find_one.side_effect = Exception("DB Error")

        with pytest.raises(Exception) as exc_info:
            trainer_repo.get_profile("user@example.com")

        assert "DB Error" in str(exc_info.value)

    def test_save_multiple_users_different_trainers(self, trainer_repo, mock_db):
        """Test saving profiles for multiple users."""
        users_and_trainers = [
            ("user1@example.com", "atlas"),
            ("user2@example.com", "luna"),
            ("user3@example.com", "sofia"),
        ]

        for email, trainer_type in users_and_trainers:
            mock_db.__getitem__.return_value.reset_mock()
            mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
            mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

            profile = TrainerProfile(
                user_email=email,
                trainer_type=trainer_type
            )
            trainer_repo.save_profile(profile)

            collection = mock_db.__getitem__.return_value
            call_args = collection.update_one.call_args
            filter_doc = call_args[0][0]

            assert filter_doc["user_email"] == email

    def test_get_profile_with_invalid_trainer_type(self, trainer_repo, mock_db):
        """Test retrieving profile with unexpected trainer type."""
        # Note: This tests the repository behavior, not validation
        # (validation should happen in service layer)
        mock_db.__getitem__.return_value.find_one.return_value = {
            "user_email": "user@example.com",
            "trainer_type": "unknown_trainer"
        }

        result = trainer_repo.get_profile("user@example.com")

        # Repository should still return the data as-is
        assert result.trainer_type == "unknown_trainer"

    def test_concurrent_saves_same_user(self, trainer_repo, mock_db):
        """Test concurrent save attempts for same user."""
        profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="atlas"
        )

        # Simulate concurrent saves
        for _ in range(3):
            mock_db.__getitem__.return_value.reset_mock()
            mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
            mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0

            trainer_repo.save_profile(profile)

        collection = mock_db.__getitem__.return_value
        # All should hit the database
        assert collection.update_one.call_count >= 1


class TestTrainerRepositoryIntegration:
    """Test integration scenarios."""

    def test_save_and_retrieve_workflow(self, trainer_repo, mock_db):
        """Test save followed by retrieve."""
        profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="luna"
        )

        # Save
        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = "123"
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 0
        trainer_repo.save_profile(profile)

        # Retrieve
        mock_db.__getitem__.return_value.reset_mock()
        mock_db.__getitem__.return_value.find_one.return_value = profile.model_dump()
        result = trainer_repo.get_profile("user@example.com")

        assert result.trainer_type == "luna"

    def test_update_and_retrieve_workflow(self, trainer_repo, mock_db):
        """Test update followed by retrieve."""
        # Initial profile
        initial_profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="atlas"
        )

        mock_db.__getitem__.return_value.update_one.return_value.upserted_id = None
        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1

        trainer_repo.save_profile(initial_profile)

        # Update profile
        mock_db.__getitem__.return_value.reset_mock()
        updated_profile = TrainerProfile(
            user_email="user@example.com",
            trainer_type="sofia"
        )

        mock_db.__getitem__.return_value.update_one.return_value.modified_count = 1
        trainer_repo.save_profile(updated_profile)

        # Retrieve updated
        mock_db.__getitem__.return_value.reset_mock()
        mock_db.__getitem__.return_value.find_one.return_value = updated_profile.model_dump()
        result = trainer_repo.get_profile("user@example.com")

        assert result.trainer_type == "sofia"
