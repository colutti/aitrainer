"""Tests for admin memory endpoints."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.auth import verify_admin
from src.core.deps import get_mongo_database


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_admin_user():
    """Mock admin user."""
    return "admin@test.com"


@pytest.fixture
def mock_mongo_db():
    """Mock MongoDB database."""
    db = MagicMock()
    db.users = MagicMock()
    db.users.get_profile = MagicMock()
    db.chat = MagicMock()
    db.chat.get_history = MagicMock()
    return db


class TestAdminMemory:
    """Test admin memory endpoints."""

    def test_get_user_messages_success(self, client, mock_admin_user, mock_mongo_db):
        """Test retrieving user messages."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        user_profile = MagicMock()
        mock_mongo_db.users.get_profile.return_value = user_profile
        
        messages = [
            MagicMock(model_dump=lambda: {"content": "Hi", "role": "user"}),
            MagicMock(model_dump=lambda: {"content": "Hello", "role": "assistant"}),
        ]
        mock_mongo_db.chat.get_history.return_value = messages
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/memory/user@test.com/messages?limit=50")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert data["user_email"] == "user@test.com"
        app.dependency_overrides = {}

    def test_get_user_messages_user_not_found(self, client, mock_admin_user, mock_mongo_db):
        """Test retrieving messages for non-existent user."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.users.get_profile.return_value = None
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/memory/nonexistent@test.com/messages")

        assert response.status_code == 404
        app.dependency_overrides = {}

    def test_get_user_messages_empty(self, client, mock_admin_user, mock_mongo_db):
        """Test retrieving messages when none exist."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        user_profile = MagicMock()
        mock_mongo_db.users.get_profile.return_value = user_profile
        mock_mongo_db.chat.get_history.return_value = []
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/memory/user@test.com/messages")

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 0
        assert data["total"] == 0
        app.dependency_overrides = {}

    def test_get_user_messages_custom_limit(self, client, mock_admin_user, mock_mongo_db):
        """Test retrieving messages with custom limit."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        user_profile = MagicMock()
        mock_mongo_db.users.get_profile.return_value = user_profile
        mock_mongo_db.chat.get_history.return_value = []
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/memory/user@test.com/messages?limit=100")

        assert response.status_code == 200
        # Verify limit was passed
        mock_mongo_db.chat.get_history.assert_called_with("user@test.com", limit=100)
        app.dependency_overrides = {}
