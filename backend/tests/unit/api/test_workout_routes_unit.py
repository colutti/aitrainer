from unittest.mock import MagicMock

from src.api.endpoints.workout import (
    CreateWorkoutRequest,
    ExerciseLog,
    create_workout,
    get_exercises,
)


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
