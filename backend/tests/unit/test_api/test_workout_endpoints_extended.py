"""
Comprehensive tests for workout endpoints.
Tests cover listing, filtering, type retrieval, and deletion operations.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from datetime import date, timedelta

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_log import WorkoutWithId


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_workout_log():
    return {
        "_id": "workout_001",
        "user_email": "test@example.com",
        "date": "2024-01-29",
        "workout_type": "strength",
        "duration_minutes": 60,
        "exercises": [
            {"name": "Bench Press", "sets": 4, "reps": 8}
        ],
        "notes": "Great session"
    }


@pytest.fixture
def sample_workout_logs():
    """Generate sample workout logs."""
    workouts = []
    for i in range(5):
        log_date = date.today() - timedelta(days=i)
        workouts.append({
            "_id": f"workout_{i:03d}",
            "user_email": "test@example.com",
            "date": str(log_date),
            "workout_type": ["strength", "cardio", "flexibility"][i % 3],
            "duration_minutes": 45 + (i * 5),
            "exercises": [],
            "notes": f"Workout {i}"
        })
    return workouts


# Test: GET /workout/list - Success Case
def test_list_workouts_success(sample_workout_logs):
    """Test retrieving paginated workout logs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workouts_paginated.return_value = (sample_workout_logs[:3], 5)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["workouts"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1

    app.dependency_overrides = {}


# Test: GET /workout/list - Multiple Pages
def test_list_workouts_pagination():
    """Test pagination with multiple pages."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()

    logs = [{"_id": f"w_{i}", "user_email": "test@example.com",
             "date": str(date.today() - timedelta(days=i))}
            for i in range(10)]
    mock_db.get_workouts_paginated.return_value = (logs, 25)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/list?page=2&page_size=10",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert data["total_pages"] == 3

    app.dependency_overrides = {}


# Test: GET /workout/list - Filter by Type
def test_list_workouts_filter_by_type():
    """Test filtering workouts by type."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workouts_paginated.return_value = ([], 0)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/list?workout_type=strength",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    call_kwargs = mock_db.get_workouts_paginated.call_args[1]
    assert call_kwargs["workout_type"] == "strength"

    app.dependency_overrides = {}


# Test: GET /workout/list - Unauthorized
def test_list_workouts_unauthorized():
    """Test workout list without authentication."""
    response = client.get("/workout/list")
    assert response.status_code == 403


# Test: GET /workout/list - Database Error
def test_list_workouts_database_error():
    """Test workout list when database error occurs."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workouts_paginated.side_effect = Exception("DB Error")
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500
    assert "Failed to retrieve workouts" in response.json()["detail"]

    app.dependency_overrides = {}


# Test: GET /workout/types - Success Case
def test_get_workout_types_success():
    """Test retrieving distinct workout types."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_types.return_value = ["strength", "cardio", "flexibility"]
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/types",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert "strength" in data

    app.dependency_overrides = {}


# Test: GET /workout/types - No Types (User New)
def test_get_workout_types_empty():
    """Test retrieving types when user has no workouts."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_types.return_value = []
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/types",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data == []

    app.dependency_overrides = {}


# Test: GET /workout/types - Unauthorized
def test_get_workout_types_unauthorized():
    """Test workout types without authentication."""
    response = client.get("/workout/types")
    assert response.status_code == 403


# Test: GET /workout/types - Database Error
def test_get_workout_types_database_error():
    """Test types retrieval with database error."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_types.side_effect = Exception("DB Error")
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/types",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 500

    app.dependency_overrides = {}


# Test: DELETE /workout/{workout_id} - Success
def test_delete_workout_success(sample_workout_log):
    """Test successful deletion of workout."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_by_id.return_value = sample_workout_log
    mock_db.delete_workout_log.return_value = True
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/workout/workout_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "deleted successfully" in data["message"]
    mock_db.delete_workout_log.assert_called_once_with("workout_001")

    app.dependency_overrides = {}


# Test: DELETE /workout/{workout_id} - Not Found
def test_delete_workout_not_found():
    """Test deleting non-existent workout."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_by_id.return_value = None
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/workout/nonexistent",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


# Test: DELETE /workout/{workout_id} - Unauthorized Owner
def test_delete_workout_unauthorized_owner():
    """Test deleting workout owned by another user."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_by_id.return_value = {
        "_id": "workout_001",
        "user_email": "other@example.com"
    }
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/workout/workout_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 403

    app.dependency_overrides = {}


# Test: DELETE /workout/{workout_id} - Unauthorized (No Token)
def test_delete_workout_unauthorized():
    """Test deletion without authentication."""
    response = client.delete("/workout/workout_001")
    assert response.status_code == 403


# Test: DELETE /workout/{workout_id} - Database Error
def test_delete_workout_database_error():
    """Test deletion when delete operation fails."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    mock_db.get_workout_by_id.return_value = {
        "_id": "workout_001",
        "user_email": "test@example.com"
    }
    mock_db.delete_workout_log.return_value = False
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.delete(
        "/workout/workout_001",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404

    app.dependency_overrides = {}


# Test: GET /workout/list - Invalid Pagination
def test_list_workouts_invalid_pagination():
    """Test with invalid pagination parameters."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_db = MagicMock()
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    # page_size exceeds maximum (51 > 50)
    response = client.get(
        "/workout/list?page_size=51",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422

    app.dependency_overrides = {}


# Test: GET /workout/list - Empty Results
def test_list_workouts_empty():
    """Test workout list with no results."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_db = MagicMock()
    mock_db.get_workouts_paginated.return_value = ([], 0)
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.get(
        "/workout/list",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workouts"] == []
    assert data["total"] == 0

    app.dependency_overrides = {}
