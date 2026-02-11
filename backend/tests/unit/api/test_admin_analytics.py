"""Tests for admin analytics endpoints."""

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
    db.database = MagicMock()
    db.database.users = MagicMock()
    db.database.message_store = MagicMock()
    db.database.workout_logs = MagicMock()
    db.database.nutrition_logs = MagicMock()
    db.database.prompt_logs = MagicMock()
    return db


class TestAdminAnalytics:
    """Test admin analytics endpoints."""

    def test_get_overview_success(self, client, mock_admin_user, mock_mongo_db):
        """Test successful retrieval of system overview."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.database.users.count_documents.return_value = 10
        mock_mongo_db.database.message_store.count_documents.return_value = 50
        mock_mongo_db.database.message_store.distinct.return_value = ["user1", "user2"]
        mock_mongo_db.database.workout_logs.count_documents.return_value = 25
        mock_mongo_db.database.nutrition_logs.count_documents.return_value = 100
        mock_mongo_db.database.prompt_logs.distinct.side_effect = [
            ["user1", "user2"],  # 7 days - 2 users
            ["user1"]  # 24 hours - 1 user
        ]

        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/analytics/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 10
        assert data["total_messages"] == 50
        assert data["total_workouts"] == 25
        assert data["total_nutrition_logs"] == 100
        assert data["active_users_total"] == 2
        assert data["active_users_7d"] == 2
        assert data["active_users_24h"] == 1
        assert "timestamp" in data
        app.dependency_overrides = {}

    def test_get_overview_no_admin(self, client, mock_mongo_db):
        """Test overview fails without admin auth."""
        app.dependency_overrides[verify_admin] = MagicMock(side_effect=Exception("Not admin"))
        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/analytics/overview")

        # Should fail due to auth
        assert response.status_code >= 400
        app.dependency_overrides = {}

    def test_get_overview_empty_data(self, client, mock_admin_user, mock_mongo_db):
        """Test overview with no data in system."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user
        mock_mongo_db.database.users.count_documents.return_value = 0
        mock_mongo_db.database.message_store.count_documents.return_value = 0
        mock_mongo_db.database.message_store.distinct.return_value = []
        mock_mongo_db.database.workout_logs.count_documents.return_value = 0
        mock_mongo_db.database.nutrition_logs.count_documents.return_value = 0
        mock_mongo_db.database.prompt_logs.distinct.side_effect = [[], [], []]

        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/analytics/overview")

        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 0
        assert data["active_users_24h"] == 0
        app.dependency_overrides = {}

    def test_get_quality_metrics_success(self, client, mock_admin_user, mock_mongo_db):
        """Test quality metrics endpoint."""
        app.dependency_overrides[verify_admin] = lambda: mock_admin_user

        # Mock message_store aggregation for avg_messages
        mock_msg_result = [{'avg': 5.5}]
        mock_mongo_db.database.message_store.aggregate.return_value = mock_msg_result

        # Mock trainer_profiles aggregation
        mock_trainer_result = [
            {'_id': 'atlas', 'count': 10},
            {'_id': 'luna', 'count': 8}
        ]
        mock_mongo_db.database.trainer_profiles.aggregate.return_value = mock_trainer_result

        # Mock users aggregation for goals
        mock_goals_result = [
            {'_id': 'weight_loss', 'count': 15},
            {'_id': 'muscle_gain', 'count': 5}
        ]
        mock_mongo_db.database.users.aggregate.return_value = mock_goals_result
        mock_mongo_db.database.users.count_documents.return_value = 20  # total users

        # Mock distinct calls
        mock_mongo_db.database.workout_logs.distinct.return_value = ["user1", "user2", "user3"]
        mock_mongo_db.database.nutrition_logs.distinct.return_value = ["user1", "user2"]

        app.dependency_overrides[get_mongo_database] = lambda: mock_mongo_db

        response = client.get("/admin/analytics/quality-metrics")

        assert response.status_code == 200
        data = response.json()
        assert "avg_messages_per_user" in data
        assert "trainer_distribution" in data
        assert "goal_distribution" in data
        assert "workout_engagement_rate" in data
        assert data["users_with_workouts"] == 3
        assert data["users_with_nutrition"] == 2
        app.dependency_overrides = {}
