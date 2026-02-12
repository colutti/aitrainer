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
