from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.api.endpoints.workout import (
    CreateWorkoutRequest,
    ExerciseLog,
    create_workout,
    get_exercises,
)
from src.api.main import app
from src.core.deps import get_mongo_database
from src.services.auth import verify_token
from src.api.models.user_profile import UserProfile


def test_get_exercises_returns_distinct_names():
    mock_db = MagicMock()
    mock_db.get_workout_exercise_names.return_value = ["Bench Press", "Squat"]

    result = get_exercises("test@example.com", mock_db)

    assert result == ["Bench Press", "Squat"]
    mock_db.get_workout_exercise_names.assert_called_once_with("test@example.com")


def test_create_workout_builds_manual_workout_log():
    mock_db = MagicMock()
    mock_db.save_workout_log.return_value = "workout123"
    mock_db.get_workout_by_id.return_value = {
        "_id": "workout123",
        "user_email": "test@example.com",
        "date": "2024-01-01T10:00:00",
        "workout_type": "Push",
        "duration_minutes": 45,
        "source": "manual",
        "external_id": None,
        "exercises": [
            {
                "name": "Bench Press",
                "sets": 2,
                "reps_per_set": [10, 8],
                "weights_per_set": [60.0, 70.0],
            }
        ],
    }

    request = CreateWorkoutRequest(
        date="2024-01-01T10:00:00",
        workout_type="Push",
        duration_minutes=45,
        source="manual",
        exercises=[
            ExerciseLog(
                name="Bench Press",
                sets=2,
                reps_per_set=[10, 8],
                weights_per_set=[60.0, 70.0],
            )
        ],
    )

    result = create_workout("test@example.com", mock_db, request)

    assert result.id == "workout123"
    assert result.source == "manual"
    assert result.workout_type == "Push"
    saved_workout = mock_db.save_workout_log.call_args.args[0]
    assert saved_workout.user_email == "test@example.com"
    assert saved_workout.source == "manual"


def test_create_workout_rejects_demo_user():
    """Demo users cannot create workouts."""
    client = TestClient(app)
    app.dependency_overrides[verify_token] = lambda: "demo@example.com"
    mock_db = MagicMock()
    mock_db.get_user_profile.return_value = UserProfile(
        email="demo@example.com",
        gender="Masculino",
        age=30,
        weight=75.0,
        height=180,
        goal_type="maintain",
        weekly_rate=0.5,
        is_demo=True,
    )
    app.dependency_overrides[get_mongo_database] = lambda: mock_db

    response = client.post(
        "/workout",
        json={
            "date": "2024-01-01T10:00:00",
            "workout_type": "Push",
            "duration_minutes": 45,
            "source": "manual",
            "exercises": [
                {
                    "name": "Bench Press",
                    "sets": 2,
                    "reps_per_set": [10, 8],
                    "weights_per_set": [60.0, 70.0],
                }
            ],
        },
        headers={"Authorization": "Bearer demo_token"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "demo_read_only"
    mock_db.save_workout_log.assert_not_called()

    app.dependency_overrides = {}
