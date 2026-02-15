"""
Tests for HevyService payload preparation.

Tests the _prepare_routine_payload method to ensure it correctly
removes forbidden fields before sending to Hevy API.
"""

import pytest
from src.services.hevy_service import HevyService


class TestPrepareRoutinePayload:
    """Test _prepare_routine_payload method"""

    def test_removes_index_from_exercises(self):
        """Should remove index field from exercises"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "index": 0,  # Should be removed
                    "sets": [{"type": "normal", "weight_kg": 80}]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        assert "index" not in cleaned["exercises"][0]
        assert cleaned["exercises"][0]["exercise_template_id"] == "ABC123"

    def test_removes_index_from_sets(self):
        """Should remove index field from sets"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "sets": [
                        {"type": "normal", "weight_kg": 80, "index": 0}  # Should be removed
                    ]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        assert "index" not in cleaned["exercises"][0]["sets"][0]
        assert cleaned["exercises"][0]["sets"][0]["weight_kg"] == 80

    def test_removes_title_from_exercises(self):
        """Should remove title field from individual exercises"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "title": "Bench Press",  # Should be removed
                    "sets": [{"type": "normal", "weight_kg": 80}]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        assert "title" not in cleaned["exercises"][0]
        assert cleaned["title"] == "Test Routine"  # Routine title should remain

    def test_removes_folder_id_when_for_update_true(self):
        """Should remove folder_id when for_update=True (PUT request)"""
        routine_data = {
            "title": "Test Routine",
            "folder_id": 123,  # Should be removed for PUT
            "exercises": []
        }

        cleaned = HevyService._prepare_routine_payload(routine_data, for_update=True)

        assert "folder_id" not in cleaned

    def test_keeps_folder_id_when_for_update_false(self):
        """Should keep folder_id when for_update=False (POST request)"""
        routine_data = {
            "title": "Test Routine",
            "folder_id": 123,  # Should be kept for POST
            "exercises": []
        }

        cleaned = HevyService._prepare_routine_payload(routine_data, for_update=False)

        assert cleaned["folder_id"] == 123

    def test_handles_multiple_exercises(self):
        """Should clean all exercises in list"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "index": 0,
                    "title": "Exercise 1",
                    "sets": [{"type": "normal", "weight_kg": 80, "index": 0}]
                },
                {
                    "exercise_template_id": "DEF456",
                    "index": 1,
                    "title": "Exercise 2",
                    "sets": [{"type": "normal", "weight_kg": 70, "index": 0}]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        # Check both exercises cleaned
        for ex in cleaned["exercises"]:
            assert "index" not in ex
            assert "title" not in ex
            for s in ex["sets"]:
                assert "index" not in s

    def test_handles_multiple_sets_per_exercise(self):
        """Should clean all sets in each exercise"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "sets": [
                        {"type": "warmup", "weight_kg": 40, "index": 0},
                        {"type": "normal", "weight_kg": 80, "index": 1},
                        {"type": "normal", "weight_kg": 80, "index": 2}
                    ]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        # Check all sets cleaned
        for s in cleaned["exercises"][0]["sets"]:
            assert "index" not in s

    def test_preserves_important_fields(self):
        """Should preserve important fields like rest_seconds, superset_id, rep_range"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "rest_seconds": 90,
                    "superset_id": 1,
                    "notes": "Focus on form",
                    "sets": [
                        {
                            "type": "normal",
                            "weight_kg": 80,
                            "rep_range": {"start": 8, "end": 12}
                        }
                    ]
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        ex = cleaned["exercises"][0]
        assert ex["rest_seconds"] == 90
        assert ex["superset_id"] == 1
        assert ex["notes"] == "Focus on form"
        assert ex["sets"][0]["rep_range"] == {"start": 8, "end": 12}

    def test_handles_empty_exercises_list(self):
        """Should handle empty exercises list gracefully"""
        routine_data = {
            "title": "Test Routine",
            "exercises": []
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        assert cleaned["exercises"] == []

    def test_handles_exercises_without_sets(self):
        """Should handle exercises without sets field"""
        routine_data = {
            "title": "Test Routine",
            "exercises": [
                {
                    "exercise_template_id": "ABC123",
                    "index": 0
                    # No sets field
                }
            ]
        }

        cleaned = HevyService._prepare_routine_payload(routine_data)

        assert "index" not in cleaned["exercises"][0]
        assert "sets" not in cleaned["exercises"][0]

    def test_full_put_payload_example(self):
        """Full example of a cleaned PUT payload"""
        # This is what GET returns
        routine_data = {
            "title": "My Routine",
            "folder_id": 123,
            "exercises": [
                {
                    "index": 0,
                    "exercise_template_id": "ABC123",
                    "title": "Bench Press",
                    "rest_seconds": 90,
                    "superset_id": None,
                    "sets": [
                        {
                            "index": 0,
                            "type": "warmup",
                            "weight_kg": 40,
                            "reps": 10
                        },
                        {
                            "index": 1,
                            "type": "normal",
                            "weight_kg": 80,
                            "rep_range": {"start": 8, "end": 12}
                        }
                    ]
                }
            ]
        }

        # Clean for PUT
        cleaned = HevyService._prepare_routine_payload(routine_data, for_update=True)

        # Verify cleaned structure ready for API
        assert "folder_id" not in cleaned
        assert cleaned["title"] == "My Routine"
        assert len(cleaned["exercises"]) == 1

        ex = cleaned["exercises"][0]
        assert "index" not in ex
        assert "title" not in ex
        assert ex["exercise_template_id"] == "ABC123"
        assert ex["rest_seconds"] == 90
        assert len(ex["sets"]) == 2

        # Verify sets are cleaned
        for s in ex["sets"]:
            assert "index" not in s
            assert "type" in s


class TestTransformToWorkoutLogCardio:
    """Test transform_to_workout_log with cardio exercises"""

    def test_treadmill_exercise_with_distance_and_duration(self):
        """Should correctly map treadmill exercise with distance and duration"""
        from src.services.hevy_service import HevyService
        from unittest.mock import Mock

        mock_repo = Mock()
        service = HevyService(workout_repository=mock_repo)

        hevy_workout = {
            "id": "workout-123",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:30:00Z",
            "title": "Cardio Session",
            "exercises": [
                {
                    "title": "Treadmill",
                    "sets": [
                        {
                            "type": "normal",
                            "reps": None,
                            "weight_kg": None,
                            "distance_meters": 1000.0,
                            "duration_seconds": 300
                        },
                        {
                            "type": "normal",
                            "reps": None,
                            "weight_kg": None,
                            "distance_meters": 1200.0,
                            "duration_seconds": 360
                        }
                    ]
                }
            ]
        }

        result = service.transform_to_workout_log(hevy_workout, "user@example.com")

        assert result is not None
        assert len(result.exercises) == 1
        exercise = result.exercises[0]
        assert exercise.name == "Treadmill"
        assert exercise.sets == 2
        assert exercise.distance_meters_per_set == [1000.0, 1200.0]
        assert exercise.duration_seconds_per_set == [300, 360]
        # Reps should be 0 when None in Hevy, but weights should be empty for pure cardio
        assert exercise.reps_per_set == [0, 0]
        assert exercise.weights_per_set == []  # Empty for pure cardio

    def test_mixed_exercise_with_reps_and_distance(self):
        """Should handle exercise with both reps and distance in same set"""
        from src.services.hevy_service import HevyService
        from unittest.mock import Mock

        mock_repo = Mock()
        service = HevyService(workout_repository=mock_repo)

        hevy_workout = {
            "id": "workout-456",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:45:00Z",
            "title": "Mixed Workout",
            "exercises": [
                {
                    "title": "Row Machine",
                    "sets": [
                        {
                            "type": "normal",
                            "reps": 20,
                            "weight_kg": 0.0,
                            "distance_meters": 500.0,
                            "duration_seconds": 120
                        }
                    ]
                }
            ]
        }

        result = service.transform_to_workout_log(hevy_workout, "user@example.com")

        assert result is not None
        exercise = result.exercises[0]
        assert exercise.reps_per_set == [20]
        assert exercise.distance_meters_per_set == [500.0]
        assert exercise.duration_seconds_per_set == [120]

    def test_multiple_exercises_mixed_cardio_strength(self):
        """Should handle workout with both strength and cardio exercises"""
        from src.services.hevy_service import HevyService
        from unittest.mock import Mock

        mock_repo = Mock()
        service = HevyService(workout_repository=mock_repo)

        hevy_workout = {
            "id": "workout-789",
            "start_time": "2024-01-15T09:00:00Z",
            "end_time": "2024-01-15T10:00:00Z",
            "title": "Full Body",
            "exercises": [
                {
                    "title": "Bench Press",
                    "sets": [
                        {
                            "type": "normal",
                            "reps": 10,
                            "weight_kg": 80.0,
                            "distance_meters": None,
                            "duration_seconds": None
                        }
                    ]
                },
                {
                    "title": "Bike",
                    "sets": [
                        {
                            "type": "normal",
                            "reps": None,
                            "weight_kg": None,
                            "distance_meters": 2000.0,
                            "duration_seconds": 480
                        }
                    ]
                }
            ]
        }

        result = service.transform_to_workout_log(hevy_workout, "user@example.com")

        assert result is not None
        assert len(result.exercises) == 2

        # Strength exercise
        strength = result.exercises[0]
        assert strength.name == "Bench Press"
        assert strength.reps_per_set == [10]
        assert strength.weights_per_set == [80.0]
        assert strength.distance_meters_per_set == []  # No cardio data for strength exercise
        assert strength.duration_seconds_per_set == []  # No cardio data for strength exercise

        # Cardio exercise
        cardio = result.exercises[1]
        assert cardio.name == "Bike"
        assert cardio.reps_per_set == [0]
        assert cardio.weights_per_set == []  # Empty for pure cardio
        assert cardio.distance_meters_per_set == [2000.0]
        assert cardio.duration_seconds_per_set == [480]
