"""
Tests for database error handling and edge cases in src/services/database.py
"""
import pytest
from unittest.mock import patch, MagicMock
from pymongo.errors import ConnectionFailure, PyMongoError
from src.services.database import MongoDatabase
from src.api.models.user_profile import UserProfile
from src.api.models.trainer_profile import TrainerProfile
from src.api.models.sender import Sender

@pytest.fixture
def mock_settings():
    with patch('src.services.database.settings') as settings:
        settings.MONGO_URI = "mongodb://test"
        settings.DB_NAME = "test_db"
        yield settings

def test_init_connection_failure(mock_settings):
    """Test database initialization failure."""
    with patch('pymongo.MongoClient') as mock_client:
        mock_client.side_effect = ConnectionFailure("Connection timed out")
        
        with pytest.raises(ConnectionFailure):
            MongoDatabase()

def test_save_user_profile_upsert_new(mock_settings):
    """Test saving a new user profile (upserted)."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        # Mock result for new insert
        mock_result = MagicMock()
        mock_result.upserted_id = "new_id"
        mock_result.modified_count = 0
        db_mock.users.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = UserProfile(
            email="test@test.com",
            password_hash="hash",
            age=25,
            weight=70.0,
            height=175.0,
            goal="Test goal with more than 5 chars",
            gender="Masculino"
        )
        
        mongo.save_user_profile(profile)
        db_mock.users.update_one.assert_called_once()

def test_save_user_profile_update_existing(mock_settings):
    """Test updating an existing user profile."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        # Mock result for update
        mock_result = MagicMock()
        mock_result.upserted_id = None
        mock_result.modified_count = 1
        db_mock.users.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = UserProfile(
            email="test@test.com",
            password_hash="hash",
            age=25,
            weight=70.0,
            height=175.0,
            goal="Test goal with more than 5 chars",
            gender="Masculino"
        )
        
        mongo.save_user_profile(profile)
        db_mock.users.update_one.assert_called_once()

def test_save_user_profile_no_changes(mock_settings):
    """Test saving user profile with no changes."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        # Mock result for no change
        mock_result = MagicMock()
        mock_result.upserted_id = None
        mock_result.modified_count = 0
        db_mock.users.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = UserProfile(
            email="test@test.com",
            password_hash="hash",
            age=25,
            weight=70.0,
            height=175.0,
            goal="Test goal with more than 5 chars",
            gender="Masculino"
        )
        
        mongo.save_user_profile(profile)
        db_mock.users.update_one.assert_called_once()

def test_save_trainer_profile_upsert_new(mock_settings):
    """Test saving a new trainer profile."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        mock_result = MagicMock()
        mock_result.upserted_id = "new_id"
        mock_result.modified_count = 0
        db_mock.trainer_profiles.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = TrainerProfile(user_email="test@test.com", trainer_type="atlas")
        
        mongo.save_trainer_profile(profile)
        db_mock.trainer_profiles.update_one.assert_called_once()

def test_save_trainer_profile_update(mock_settings):
    """Test updating existing trainer profile."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        mock_result = MagicMock()
        mock_result.upserted_id = None
        mock_result.modified_count = 1
        db_mock.trainer_profiles.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = TrainerProfile(user_email="test@test.com", trainer_type="atlas")
        
        mongo.save_trainer_profile(profile)
        db_mock.trainer_profiles.update_one.assert_called_once()

def test_save_trainer_profile_no_changes(mock_settings):
    """Test saving trainer profile with no changes."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        mock_result = MagicMock()
        mock_result.upserted_id = None
        mock_result.modified_count = 0
        db_mock.trainer_profiles.update_one.return_value = mock_result
        
        mongo = MongoDatabase()
        profile = TrainerProfile(user_email="test@test.com", trainer_type="atlas")
        
        mongo.save_trainer_profile(profile)
        db_mock.trainer_profiles.update_one.assert_called_once()

def test_get_user_profile_not_found(mock_settings):
    """Test getting non-existent user profile."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        db_mock.users.find_one.return_value = None
        
        mongo = MongoDatabase()
        result = mongo.get_user_profile("exists@not.com")
        assert result is None

def test_validate_user_not_found(mock_settings):
    """Test validating non-existent user."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        db_mock.users.find_one.return_value = None
        
        mongo = MongoDatabase()
        assert mongo.validate_user("email", "pass") is False

def test_validate_user_wrong_password(mock_settings):
    """Test validating user with wrong password."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        # Fake bcrypt hash
        db_mock.users.find_one.return_value = {"password_hash": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxwKc.6q.1"} 
        
        mongo = MongoDatabase()
        with patch('bcrypt.checkpw', return_value=False):
            assert mongo.validate_user("email", "wrongpass") is False

def test_get_trainer_profile_not_found(mock_settings):
    """Test getting non-existent trainer profile."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        db_mock.trainer_profiles.find_one.return_value = None
        
        mongo = MongoDatabase()
        assert mongo.get_trainer_profile("email") is None

def test_add_to_history(mock_settings):
    """Test adding messages to chat history."""
    with patch('pymongo.MongoClient') as mock_client, \
         patch('src.services.database.MongoDBChatMessageHistory') as mock_history_cls:
        
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        mock_history_instance = MagicMock()
        mock_history_cls.return_value = mock_history_instance
        
        mongo = MongoDatabase()
        
        msg = MagicMock()
        msg.sender = Sender.STUDENT
        msg.text = "Hello"
        
        mongo.add_to_history(msg, "session_id")
        
        mock_history_instance.add_message.assert_called_once()
        
        # Test trainer message
        msg.sender = Sender.TRAINER
        mongo.add_to_history(msg, "session_id", trainer_type="atlas")
        assert mock_history_instance.add_message.call_count == 2

def test_get_conversation_memory(mock_settings):
    """Test creating conversation summary buffer memory."""
    with patch('pymongo.MongoClient') as mock_client, \
         patch('src.services.database.MongoDBChatMessageHistory') as mock_history_cls, \
         patch('src.services.database.ConversationSummaryBufferMemory') as mock_memory_cls:
        
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        mongo = MongoDatabase()
        llm = MagicMock()
        
        mongo.get_conversation_memory("session_id", llm)
        
        mock_memory_cls.assert_called_once()
        call_kwargs = mock_memory_cls.call_args[1]
        assert call_kwargs["llm"] == llm
        assert "chat_memory" in call_kwargs

def test_get_workout_logs(mock_settings):
    """Test retrieving workout logs."""
    with patch('pymongo.MongoClient') as mock_client:
        db_mock = MagicMock()
        mock_client.return_value = {mock_settings.DB_NAME: db_mock}
        
        # Mock cursor
        mock_cursor = MagicMock()
        db_mock.workout_logs.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        
        # Mock docs
        mock_cursor.__iter__.return_value = [
            {
                "id": "1",
                "user_email": "test@test.com",
                "date": "2024-01-01T10:00:00",
                "exercises": [],
                "workout_type": "Push",
                "duration_minutes": 60,
                "notes": "Good"
            }
        ]
        
        mongo = MongoDatabase()
        workouts = mongo.get_workout_logs("test@test.com")
        
        assert len(workouts) == 1
        assert workouts[0].workout_type == "Push"
