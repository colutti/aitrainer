"""
Comprehensive tests for workout statistics endpoints.
Tests cover dashboard stats retrieval and aggregated workout metrics.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_stats import WorkoutStats


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_workout_stats():
    return WorkoutStats(
        total_workouts=42,
        total_duration_minutes=2520,
        total_exercises=156,
        average_workout_duration=60,
        most_frequent_type="strength",
        workouts_this_week=5,
        total_sets=420,
        total_reps=5040,
        avg_sets_per_workout=10,
        avg_reps_per_workout=120
    )


# Test: GET /stats/stats - Success Case
def test_get_dashboard_stats_success(sample_workout_stats):
    """Test retrieving dashboard workout statistics."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = sample_workout_stats
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 42
    assert data["average_workout_duration"] == 60
    assert data["most_frequent_type"] == "strength"
    assert data["workouts_this_week"] == 5

    mock_db.get_workout_stats.assert_called_once_with("test@example.com")

    app.dependency_overrides = {}


# Test: GET /stats/stats - New User (No Data)
def test_get_dashboard_stats_no_data():
    """Test stats for new user with no workout data."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = WorkoutStats(
        total_workouts=0,
        total_duration_minutes=0,
        total_exercises=0,
        average_workout_duration=0,
        most_frequent_type=None,
        workouts_this_week=0,
        total_sets=0,
        total_reps=0,
        avg_sets_per_workout=0,
        avg_reps_per_workout=0
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 0
    assert data["workouts_this_week"] == 0

    app.dependency_overrides = {}


# Test: GET /stats/stats - Unauthorized
def test_get_dashboard_stats_unauthorized():
    """Test stats retrieval without authentication."""
    response = client.get("/stats/stats")
    assert response.status_code == 403


# Test: GET /stats/stats - Database Error
def test_get_dashboard_stats_database_error():
    """Test stats when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.side_effect = Exception("Database connection failed")
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    data = response.json()
    assert "Failed to retrieve workout stats" in data["detail"]

    app.dependency_overrides = {}


# Test: GET /stats/stats - Large Numbers
def test_get_dashboard_stats_large_numbers():
    """Test stats with high workout volume."""
    app.dependency_overrides[verify_token] = lambda: "veteran@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = WorkoutStats(
        total_workouts=500,
        total_duration_minutes=50000,
        total_exercises=5000,
        average_workout_duration=100,
        most_frequent_type="strength",
        workouts_this_week=7,
        total_sets=10000,
        total_reps=150000,
        avg_sets_per_workout=20,
        avg_reps_per_workout=300
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 500
    assert data["total_reps"] == 150000

    app.dependency_overrides = {}


# Test: GET /stats/stats - Various Trainer Types
def test_get_dashboard_stats_various_types():
    """Test stats with different most frequent workout types."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    types = ["strength", "cardio", "flexibility", "mixed"]
    for workout_type in types:
        mock_db.get_workout_stats.return_value = WorkoutStats(
            total_workouts=30,
            total_duration_minutes=1800,
            total_exercises=100,
            average_workout_duration=60,
            most_frequent_type=workout_type,
            workouts_this_week=3,
            total_sets=200,
            total_reps=3000,
            avg_sets_per_workout=6,
            avg_reps_per_workout=100
        )
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/stats/stats",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["most_frequent_type"] == workout_type

    app.dependency_overrides = {}


# Test: GET /stats/stats - Multiple Requests
def test_get_dashboard_stats_consistency():
    """Test that multiple requests return consistent data."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    stats = WorkoutStats(
        total_workouts=42,
        total_duration_minutes=2520,
        total_exercises=156,
        average_workout_duration=60,
        most_frequent_type="strength",
        workouts_this_week=5,
        total_sets=420,
        total_reps=5040,
        avg_sets_per_workout=10,
        avg_reps_per_workout=120
    )
    mock_db.get_workout_stats.return_value = stats
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # First request
    response1 = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response1.status_code == 200
    data1 = response1.json()

    # Second request
    response2 = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response2.status_code == 200
    data2 = response2.json()

    # Data should be consistent
    assert data1 == data2
    assert mock_db.get_workout_stats.call_count == 2

    app.dependency_overrides = {}


# Test: GET /stats/stats - Response Schema
def test_get_dashboard_stats_schema():
    """Test that response matches WorkoutStats schema."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = WorkoutStats(
        total_workouts=42,
        total_duration_minutes=2520,
        total_exercises=156,
        average_workout_duration=60,
        most_frequent_type="strength",
        workouts_this_week=5,
        total_sets=420,
        total_reps=5040,
        avg_sets_per_workout=10,
        avg_reps_per_workout=120
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields are present
    required_fields = [
        "total_workouts",
        "total_duration_minutes",
        "total_exercises",
        "average_workout_duration",
        "most_frequent_type",
        "workouts_this_week",
        "total_sets",
        "total_reps",
        "avg_sets_per_workout",
        "avg_reps_per_workout"
    ]

    for field in required_fields:
        assert field in data

    app.dependency_overrides = {}


# Test: GET /stats/stats - Null Fields Handling
def test_get_dashboard_stats_null_fields():
    """Test stats when some optional fields are null."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = WorkoutStats(
        total_workouts=5,
        total_duration_minutes=300,
        total_exercises=15,
        average_workout_duration=60,
        most_frequent_type=None,  # No frequent type
        workouts_this_week=2,
        total_sets=30,
        total_reps=450,
        avg_sets_per_workout=6,
        avg_reps_per_workout=90
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/stats/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["most_frequent_type"] is None

    app.dependency_overrides = {}
