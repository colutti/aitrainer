"""Tests for admin user management endpoints."""

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
    db.users.collection = MagicMock()
    db.users.get_profile = MagicMock()
    db.users.update_profile_fields = MagicMock()
    db.database = MagicMock()
    db.database.__getitem__ = MagicMock()
    return db


class TestAdminUsers:
    """Test admin user management endpoints."""

    def test_list_users_success(self, client, mock_admin_user, mock_mongo_db):
        """Test listing users with pagination."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        mock_users = [
            {"email": "user1@test.com", "name": "User 1"},
            {"email": "user2@test.com", "name": "User 2"},
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = mock_users
        mock_mongo_db.users.collection.find.return_value = mock_cursor
        mock_mongo_db.users.collection.count_documents.return_value = 2
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/users/list?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 2
        assert data["total"] == 2
        assert data["page"] == 1
        app.dependency_overrides = {}

    def test_list_users_with_search(self, client, mock_admin_user, mock_mongo_db):
        """Test listing users with search filter."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        mock_users = [{"email": "test@test.com", "name": "Test User"}]
        
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = mock_users
        mock_mongo_db.users.collection.find.return_value = mock_cursor
        mock_mongo_db.users.collection.count_documents.return_value = 1
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/users/list?search=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 1
        app.dependency_overrides = {}

    def test_list_users_empty(self, client, mock_admin_user, mock_mongo_db):
        """Test listing users when none exist."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value.limit.return_value = []
        mock_mongo_db.users.collection.find.return_value = mock_cursor
        mock_mongo_db.users.collection.count_documents.return_value = 0
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/users/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) == 0
        assert data["total"] == 0
        app.dependency_overrides = {}

    def test_get_user_details_success(self, client, mock_admin_user, mock_mongo_db):
        """Test getting user details."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        user_profile = MagicMock()
        user_profile.email = "user@test.com"
        user_profile.name = "Test User"
        user_profile.model_dump.return_value = {
            "email": "user@test.com",
            "name": "Test User"
        }
        
        mock_mongo_db.users.get_profile.return_value = user_profile
        mock_mongo_db.database.__getitem__.return_value.count_documents.side_effect = [3, 5, 10]
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/users/user@test.com/details")

        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["email"] == "user@test.com"
        assert data["stats"]["message_count"] == 3
        app.dependency_overrides = {}

    def test_get_user_details_not_found(self, client, mock_admin_user, mock_mongo_db):
        """Test getting details for non-existent user."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.users.get_profile.return_value = None
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/users/nonexistent@test.com/details")

        assert response.status_code == 404
        app.dependency_overrides = {}

    def test_update_user_success(self, client, mock_admin_user, mock_mongo_db):
        """Test updating user profile."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.users.update_profile_fields.return_value = True
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.patch(
            "/admin/users/user@test.com",
            json={"name": "New Name"}
        )

        assert response.status_code == 200
        mock_mongo_db.users.update_profile_fields.assert_called_once()
        app.dependency_overrides = {}

    def test_update_user_protected_field(self, client, mock_admin_user, mock_mongo_db):
        """Test update fails on protected fields."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.patch(
            "/admin/users/user@test.com",
            json={"email": "new@test.com"}
        )

        assert response.status_code == 400
        app.dependency_overrides = {}

    def test_update_user_not_found(self, client, mock_admin_user, mock_mongo_db):
        """Test update fails for non-existent user."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.users.update_profile_fields.return_value = False
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.patch(
            "/admin/users/nonexistent@test.com",
            json={"name": "Name"}
        )

        assert response.status_code == 404
        app.dependency_overrides = {}
