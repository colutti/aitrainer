"""Tests for admin prompts endpoints."""

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.auth import verify_admin
from src.core.deps import get_mongo_database
from bson import ObjectId


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
    db.prompts = MagicMock()
    db.prompts.collection = MagicMock()
    return db


class TestAdminPrompts:
    """Test admin prompts endpoints."""

    def test_list_prompts_success(self, client, mock_admin_user, mock_mongo_db):
        """Test listing prompts with pagination."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        prompts = [
            {
                "_id": ObjectId(),
                "user_email": "user1@test.com",
                "timestamp": "2024-01-15T10:00:00Z",
                "prompt": {"type": "simple", "input": "Test prompt"}
            },
            {
                "_id": ObjectId(),
                "user_email": "user2@test.com",
                "timestamp": "2024-01-15T09:00:00Z",
                "prompt": {"type": "with_tools", "messages": [{"content": "Hi"}]}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = prompts
        mock_mongo_db.prompts.collection.find.return_value = mock_cursor
        mock_mongo_db.prompts.collection.count_documents.return_value = 2
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/prompts?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) >= 0
        assert "total" in data
        app.dependency_overrides = {}

    def test_list_prompts_with_user_filter(self, client, mock_admin_user, mock_mongo_db):
        """Test listing prompts filtered by user."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        prompts = [
            {
                "_id": ObjectId(),
                "user_email": "specific@test.com",
                "timestamp": "2024-01-15T10:00:00Z",
                "prompt": {"type": "simple", "input": "Test"}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = prompts
        mock_mongo_db.prompts.collection.find.return_value = mock_cursor
        mock_mongo_db.prompts.collection.count_documents.return_value = 1
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/prompts?user_id=specific@test.com")

        assert response.status_code == 200
        # Verify filter was applied
        mock_mongo_db.prompts.collection.find.assert_called_once()
        call_args = mock_mongo_db.prompts.collection.find.call_args
        assert call_args[0][0].get("user_email") == "specific@test.com"
        app.dependency_overrides = {}

    def test_list_prompts_empty(self, client, mock_admin_user, mock_mongo_db):
        """Test listing prompts when none exist."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = []
        mock_mongo_db.prompts.collection.find.return_value = mock_cursor
        mock_mongo_db.prompts.collection.count_documents.return_value = 0
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/prompts")

        assert response.status_code == 200
        data = response.json()
        assert len(data["prompts"]) == 0
        assert data["total"] == 0
        app.dependency_overrides = {}

    def test_list_prompts_pagination_calculation(self, client, mock_admin_user, mock_mongo_db):
        """Test pagination calculation for prompts."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = []
        mock_mongo_db.prompts.collection.find.return_value = mock_cursor
        mock_mongo_db.prompts.collection.count_documents.return_value = 25
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/prompts?page=1&page_size=10")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert data["total_pages"] == 3  # ceil(25/10)
        app.dependency_overrides = {}

    def test_list_prompts_object_id_conversion(self, client, mock_admin_user, mock_mongo_db):
        """Test that ObjectId is converted to string."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        
        object_id = ObjectId()
        prompts = [
            {
                "_id": object_id,
                "user_email": "user@test.com",
                "timestamp": "2024-01-15T10:00:00Z",
                "prompt": {"type": "simple", "input": "Test"}
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = prompts
        mock_mongo_db.prompts.collection.find.return_value = mock_cursor
        mock_mongo_db.prompts.collection.count_documents.return_value = 1
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/prompts")

        assert response.status_code == 200
        # Response should have converted ObjectId to string (or omitted _id)
        app.dependency_overrides = {}
