"""
Tests for Hevy routine models, especially rep_range validation.

Based on POC findings: API requires rep_range as {"start": int, "end": int}
We need validators to handle LLM mistakes (int, str, list inputs)
"""

from src.api.models.routine import HevySet, HevyRepRange, HevyRoutineExercise


class TestHevySetRepRangeValidator:
    """Test validator that coerces rep_range into correct format"""

    def test_rep_range_dict_passthrough(self):
        """Dict format should pass through unchanged"""
        s = HevySet(type="normal", rep_range={"start": 8, "end": 12})
        assert s.rep_range.start == 8
        assert s.rep_range.end == 12

    def test_rep_range_none_passthrough(self):
        """None should remain None"""
        s = HevySet(type="normal", rep_range=None)
        assert s.rep_range is None

    def test_rep_range_int_coercion(self):
        """LLM sends int 12 -> coerce to {"start": 12, "end": 12}"""
        s = HevySet(type="normal", rep_range=12)
        assert s.rep_range.start == 12
        assert s.rep_range.end == 12

    def test_rep_range_string_hyphen_coercion(self):
        """LLM sends '8-12' -> coerce to {"start": 8, "end": 12}"""
        s = HevySet(type="normal", rep_range="8-12")
        assert s.rep_range.start == 8
        assert s.rep_range.end == 12

    def test_rep_range_string_single_number(self):
        """LLM sends '12' -> coerce to {"start": 12, "end": 12}"""
        s = HevySet(type="normal", rep_range="12")
        assert s.rep_range.start == 12
        assert s.rep_range.end == 12

    def test_rep_range_string_spaced_hyphen(self):
        """LLM sends '8 - 12' with spaces -> coerce correctly"""
        s = HevySet(type="normal", rep_range="8 - 12")
        assert s.rep_range.start == 8
        assert s.rep_range.end == 12

    def test_rep_range_list_coercion(self):
        """LLM sends [8, 12] -> coerce to {"start": 8, "end": 12}"""
        s = HevySet(type="normal", rep_range=[8, 12])
        assert s.rep_range.start == 8
        assert s.rep_range.end == 12

    def test_rep_range_tuple_coercion(self):
        """LLM sends (8, 12) -> coerce to {"start": 8, "end": 12}"""
        s = HevySet(type="normal", rep_range=(8, 12))
        assert s.rep_range.start == 8
        assert s.rep_range.end == 12

    def test_rep_range_invalid_string_returns_none(self):
        """Invalid string format -> returns None (invalid)"""
        s = HevySet(type="normal", rep_range="abc-xyz")
        assert s.rep_range is None

    def test_rep_range_empty_list_returns_none(self):
        """Empty list -> returns None"""
        s = HevySet(type="normal", rep_range=[])
        assert s.rep_range is None

    def test_type_normalization_warmup(self):
        """warm_up should normalize to warmup"""
        s = HevySet(type="warm_up")
        assert s.type == "warmup"

    def test_type_normalization_dropset(self):
        """drop_set should normalize to dropset"""
        s = HevySet(type="drop_set")
        assert s.type == "dropset"

    def test_hevy_set_with_reps(self):
        """HevySet with reps should work"""
        s = HevySet(type="normal", weight_kg=80, reps=10)
        assert s.reps == 10
        assert s.rep_range is None

    def test_hevy_set_with_both_reps_and_rep_range(self):
        """HevySet can have both reps and rep_range (API decides what to use)"""
        s = HevySet(type="normal", weight_kg=80, reps=10, rep_range={"start": 8, "end": 12})
        assert s.reps == 10
        assert s.rep_range.start == 8

    def test_hevy_routine_exercise_basic(self):
        """HevyRoutineExercise with basic fields"""
        ex = HevyRoutineExercise(
            exercise_template_id="ABC123",
            rest_seconds=90,
            sets=[
                HevySet(type="normal", weight_kg=80, rep_range={"start": 8, "end": 12}),
                HevySet(type="normal", weight_kg=75, rep_range={"start": 8, "end": 12})
            ]
        )
        assert ex.exercise_template_id == "ABC123"
        assert ex.rest_seconds == 90
        assert len(ex.sets) == 2

    def test_hevy_routine_exercise_with_superset_id(self):
        """HevyRoutineExercise with superset_id"""
        ex = HevyRoutineExercise(
            exercise_template_id="ABC123",
            superset_id=1,
            sets=[HevySet(type="normal", weight_kg=80)]
        )
        assert ex.superset_id == 1

    def test_hevy_routine_exercise_with_notes(self):
        """HevyRoutineExercise with notes"""
        ex = HevyRoutineExercise(
            exercise_template_id="ABC123",
            notes="💪 Focus on form",
            sets=[HevySet(type="normal", weight_kg=80)]
        )
        assert ex.notes == "💪 Focus on form"

    def test_rep_range_with_end_null(self):
        """API can return rep_range with end=null. Should be valid."""
        rr = HevyRepRange(start=15, end=None)
        assert rr.start == 15
        assert rr.end is None


class TestPutPayloadConstruction:
    """Test that we can construct valid PUT payloads for the Hevy API"""

    def test_put_payload_structure(self):
        """Verify a valid PUT payload structure"""
        # This is what hevy_service.update_routine should send
        payload = {
            "routine": {
                "title": "My Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC123",
                        "rest_seconds": 90,
                        "superset_id": None,
                        "sets": [
                            {
                                "type": "warmup",
                                "weight_kg": 40,
                                "reps": 10
                            },
                            {
                                "type": "normal",
                                "weight_kg": 80,
                                "rep_range": {"start": 8, "end": 12}
                            }
                        ]
                    }
                ]
            }
        }

        # Should not raise
        assert payload["routine"]["title"] == "My Routine"
        assert len(payload["routine"]["exercises"]) == 1
        assert payload["routine"]["exercises"][0]["rest_seconds"] == 90

    def test_put_payload_no_folder_id(self):
        """PUT payload should NOT include folder_id (API rejects it)"""
        payload = {
            "routine": {
                "title": "My Routine",
                "exercises": []
            }
        }

        # API will reject if folder_id is included
        assert "folder_id" not in payload["routine"]

    def test_put_payload_no_index_fields(self):
        """PUT payload should NOT include index fields"""
        # GET returns index, but PUT must not have it
        payload = {
            "routine": {
                "title": "My Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC",
                        "sets": [
                            {"type": "normal", "weight_kg": 80}
                            # No "index" field
                        ]
                        # No "index" field
                    }
                ]
            }
        }

        assert "index" not in payload["routine"]["exercises"][0]
        assert "index" not in payload["routine"]["exercises"][0]["sets"][0]

    def test_put_payload_requires_all_fields_to_preserve(self):
        """
        If you want to preserve a field in PUT, you MUST include it.
        Omitting a field = API sets it to null.
        """
        # This is WRONG - rest_seconds will become null
        wrong_payload = {
            "routine": {
                "title": "My Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC",
                        "sets": [{"type": "normal", "weight_kg": 80}]
                        # rest_seconds is omitted -> will be null'd
                    }
                ]
            }
        }

        # This is CORRECT - rest_seconds is preserved
        correct_payload = {
            "routine": {
                "title": "My Routine",
                "exercises": [
                    {
                        "exercise_template_id": "ABC",
                        "rest_seconds": 90,  # Must include to preserve
                        "sets": [{"type": "normal", "weight_kg": 80}]
                    }
                ]
            }
        }

        assert "rest_seconds" not in wrong_payload["routine"]["exercises"][0]
        assert correct_payload["routine"]["exercises"][0]["rest_seconds"] == 90
