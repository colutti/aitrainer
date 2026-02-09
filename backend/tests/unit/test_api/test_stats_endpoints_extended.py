"""
Comprehensive tests for workout statistics endpoints.
Tests cover dashboard stats retrieval and aggregated workout metrics.
"""

from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest
from datetime import datetime

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_stats import WorkoutStats, VolumeStat, PersonalRecord


client = TestClient(app)


def create_workout_stats(
    total_workouts=42,
    current_streak_weeks=8,
    weekly_frequency=None,
    weekly_volume=None,
    recent_prs=None,
):
    """Helper function to create valid WorkoutStats for testing."""
    if weekly_frequency is None:
        weekly_frequency = [True, True, False, True, True, False, True]
    if weekly_volume is None:
        weekly_volume = [
            VolumeStat(category="Perna", volume=5000.0),
            VolumeStat(category="Costas", volume=4200.0),
        ]
    if recent_prs is None:
        recent_prs = [
            PersonalRecord(
                exercise_name="Supino",
                weight=120.0,
                reps=8,
                date=datetime.now(),
                workout_id="w_001"
            )
        ]

    return WorkoutStats(
        current_streak_weeks=current_streak_weeks,
        weekly_frequency=weekly_frequency,
        weekly_volume=weekly_volume,
        recent_prs=recent_prs,
        total_workouts=total_workouts,
        last_workout=None,
        volume_trend=[4800, 5100, 5200, 5000, 5300, 4900, 5100, 5200],
        strength_radar={"Perna": 0.95, "Costas": 0.88}
    )


# Fixtures
@pytest.fixture
def sample_workout_stats():
    return WorkoutStats(
        current_streak_weeks=8,
        weekly_frequency=[True, True, False, True, True, False, True],
        weekly_volume=[
            VolumeStat(category="Perna", volume=5000.0),
            VolumeStat(category="Costas", volume=4200.0),
        ],
        recent_prs=[
            PersonalRecord(
                exercise_name="Supino",
                weight=120.0,
                reps=8,
                date=datetime.now(),
                workout_id="w_001"
            )
        ],
        total_workouts=42,
        last_workout=None,
        volume_trend=[4800, 5100, 5200, 5000, 5300, 4900, 5100, 5200],
        strength_radar={"Perna": 0.95, "Costas": 0.88}
    )


# Test: GET /stats/stats - Success Case
def test_get_dashboard_stats_success(sample_workout_stats):
    """Test retrieving dashboard workout statistics."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = sample_workout_stats
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 42
    assert data["current_streak_weeks"] == 8
    assert len(data["weekly_frequency"]) == 7

    mock_db.get_workout_stats.assert_called_once_with("test@example.com")

    app.dependency_overrides = {}


# Test: GET /stats/stats - New User (No Data)
def test_get_dashboard_stats_no_data():
    """Test stats for new user with no workout data."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = create_workout_stats(total_workouts=0)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 0

    app.dependency_overrides = {}


# Test: GET /stats/stats - Unauthorized
def test_get_dashboard_stats_unauthorized():
    """Test stats retrieval without authentication."""
    response = client.get("/workout/stats")
    assert response.status_code == 401


# Test: GET /stats/stats - Database Error
def test_get_dashboard_stats_database_error():
    """Test stats when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.side_effect = Exception("Database connection failed")
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
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
    mock_db.get_workout_stats.return_value = create_workout_stats(total_workouts=500)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_workouts"] == 500

    app.dependency_overrides = {}


# Test: GET /stats/stats - Various Trainer Types
def test_get_dashboard_stats_various_types():
    """Test stats with different current streak weeks."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    streaks = [1, 4, 8, 12]
    for streak in streaks:
        mock_db.get_workout_stats.return_value = create_workout_stats(
            current_streak_weeks=streak
        )
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = client.get(
            "/workout/stats",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["current_streak_weeks"] == streak

    app.dependency_overrides = {}


# Test: GET /stats/stats - Multiple Requests
def test_get_dashboard_stats_consistency():
    """Test that multiple requests return consistent data."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    stats = create_workout_stats(total_workouts=42)
    mock_db.get_workout_stats.return_value = stats
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # First request
    response1 = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )
    assert response1.status_code == 200
    data1 = response1.json()

    # Second request
    response2 = client.get(
        "/workout/stats",
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
    mock_db.get_workout_stats.return_value = create_workout_stats(total_workouts=42)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()

    # Verify all required fields are present
    required_fields = [
        "current_streak_weeks",
        "weekly_frequency",
        "weekly_volume",
        "recent_prs",
        "total_workouts"
    ]

    for field in required_fields:
        assert field in data

    app.dependency_overrides = {}


# Test: GET /stats/stats - Null Fields Handling
def test_get_dashboard_stats_null_fields():
    """Test stats when optional fields are null."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_stats.return_value = create_workout_stats(total_workouts=5)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/stats",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["last_workout"] is None

    app.dependency_overrides = {}
