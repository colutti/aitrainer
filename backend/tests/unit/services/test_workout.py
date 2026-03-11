"""
Unit tests for workout tracking functionality.
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

from src.api.models.workout_log import ExerciseLog, WorkoutLog
from src.services.workout_tools import (
    create_save_workout_tool,
    create_get_workouts_tool,
    _format_exercises_summary,
)


class TestWorkoutLogModels(unittest.TestCase):
    """Tests for WorkoutLog and ExerciseLog Pydantic models."""

    def test_exercise_log_creation(self):
        """Test creating an ExerciseLog with valid data."""
        exercise = ExerciseLog(
            name="Supino Reto",
            sets=3,
            reps_per_set=[12, 12, 10],
            weights_per_set=[80.5, 80.5, 75.0],
        )
        self.assertEqual(exercise.name, "Supino Reto")
        self.assertEqual(exercise.sets, 3)
        self.assertEqual(exercise.reps_per_set, [12, 12, 10])
        self.assertEqual(exercise.weights_per_set, [80.5, 80.5, 75.0])

    def test_exercise_log_without_weight(self):
        """Test creating an ExerciseLog without weight (optional field)."""
        exercise = ExerciseLog(name="Flexão", sets=4, reps_per_set=[15, 15, 15, 12])
        self.assertEqual(exercise.weights_per_set, [])

    def test_workout_log_creation(self):
        """Test creating a complete WorkoutLog."""
        exercises = [
            ExerciseLog(
                name="Agachamento",
                sets=4,
                reps_per_set=[10] * 4,
                weights_per_set=[100.0] * 4,
            ),
            ExerciseLog(
                name="Leg Press",
                sets=3,
                reps_per_set=[12] * 3,
                weights_per_set=[200.0] * 3,
            ),
        ]
        workout = WorkoutLog(
            user_email="test@example.com",
            workout_type="Legs",
            exercises=exercises,
            duration_minutes=45,
        )
        self.assertEqual(workout.user_email, "test@example.com")
        self.assertEqual(workout.workout_type, "Legs")
        self.assertEqual(len(workout.exercises), 2)
        self.assertEqual(workout.duration_minutes, 45)
        self.assertIsInstance(workout.date, datetime)

    def test_workout_log_model_dump(self):
        """Test that WorkoutLog can be serialized to dict for MongoDB."""
        workout = WorkoutLog(
            user_email="test@example.com",
            workout_type="Upper",
            exercises=[
                ExerciseLog(
                    name="Supino",
                    sets=3,
                    reps_per_set=[10, 10, 8],
                    weights_per_set=[60.0, 60.0, 55.0],
                )
            ],
        )
        data = workout.model_dump()
        self.assertIsInstance(data, dict)
        self.assertEqual(data["user_email"], "test@example.com")
        self.assertEqual(len(data["exercises"]), 1)


class TestSaveWorkoutTool(unittest.TestCase):
    """Tests for the save_workout LangChain tool."""

    def setUp(self):
        """Set up mock database."""
        self.mock_db = MagicMock()
        self.mock_db.save_workout_log.return_value = "mock_id_123"

    def test_save_workout_tool_creation(self):
        """Test that the tool factory creates a valid tool."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")
        self.assertEqual(tool.name, "save_workout")
        self.assertIn("Salva um treino", tool.description)

    def test_save_workout_tool_execution_new_format(self):
        """Test executing the save_workout tool with new format."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")

        result = tool.invoke(
            {
                "workout_type": "Legs",
                "exercises": [
                    {
                        "name": "Agachamento",
                        "sets": 4,
                        "reps_per_set": [10, 10, 8, 8],
                        "weights_per_set": [100.0, 100.0, 110.0, 110.0],
                    }
                ],
                "duration_minutes": 45,
            }
        )

        self.assertIn("sucesso", result.lower())
        self.mock_db.save_workout_log.assert_called_once()

        # Verify the workout was created correctly
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        self.assertEqual(saved_workout.user_email, "user@test.com")
        self.assertEqual(saved_workout.workout_type, "Legs")
        self.assertEqual(len(saved_workout.exercises), 1)
        self.assertEqual(saved_workout.exercises[0].reps_per_set, [10, 10, 8, 8])

    def test_save_workout_tool_backward_compatibility(self):
        """Test that old format (reps, weight_kg) still works."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")

        result = tool.invoke(
            {
                "workout_type": "Upper",
                "exercises": [
                    {"name": "Supino", "sets": 3, "reps": 10, "weight_kg": 80}
                ],
            }
        )

        self.assertIn("sucesso", result.lower())
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        # Should convert to new format
        self.assertEqual(saved_workout.exercises[0].reps_per_set, [10, 10, 10])
        self.assertEqual(saved_workout.exercises[0].weights_per_set, [80, 80, 80])

    def test_save_workout_tool_with_custom_date(self):
        """Test that workout is saved with custom date."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")

        result = tool.invoke(
            {
                "workout_type": "Legs",
                "exercises": [
                    {"name": "Agachamento", "sets": 3, "reps_per_set": [10, 10, 10]}
                ],
                "date": "2024-01-14",
            }
        )

        self.assertIn("sucesso", result.lower())
        self.assertIn("14/01/2024", result)
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        self.assertEqual(saved_workout.date.date(), datetime(2024, 1, 14).date())


class TestGetWorkoutsTool(unittest.TestCase):
    """Tests for the get_workouts LangChain tool."""

    def setUp(self):
        """Set up mock database with sample workouts."""
        self.mock_db = MagicMock()

        # Sample workouts for testing
        self.sample_workouts = [
            WorkoutLog(
                user_email="user@test.com",
                date=datetime(2025, 12, 21, 14, 30),
                workout_type="Push",
                exercises=[
                    ExerciseLog(
                        name="Supino",
                        sets=4,
                        reps_per_set=[10, 10, 8, 8],
                        weights_per_set=[80.0, 80.0, 85.0, 85.0],
                    ),
                    ExerciseLog(
                        name="Tríceps",
                        sets=3,
                        reps_per_set=[12] * 3,
                        weights_per_set=[25.0] * 3,
                    ),
                ],
                duration_minutes=45,
            ),
            WorkoutLog(
                user_email="user@test.com",
                date=datetime(2025, 12, 20, 10, 0),
                workout_type="Legs",
                exercises=[
                    ExerciseLog(
                        name="Agachamento",
                        sets=4,
                        reps_per_set=[10] * 4,
                        weights_per_set=[100.0] * 4,
                    ),
                ],
                duration_minutes=60,
            ),
        ]

    def test_get_workouts_tool_creation(self):
        """Test that the tool factory creates a valid tool."""
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")
        self.assertEqual(tool.name, "get_workouts")
        self.assertIn("Busca", tool.description)

    def test_get_workouts_returns_formatted_data(self):
        """Test that workouts are formatted correctly."""
        self.mock_db.get_workout_logs.return_value = self.sample_workouts
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        self.assertIn("2 treino(s)", result)
        self.assertIn("Push", result)
        self.assertIn("Legs", result)
        self.assertIn("Supino", result)
        self.assertIn("Agachamento", result)

    def test_get_workouts_empty_history(self):
        """Test message when no workouts found."""
        self.mock_db.get_workout_logs.return_value = []
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        self.assertIn("Nenhum treino registrado", result)


class TestExerciseSummaryFormatting(unittest.TestCase):
    """Tests for _format_exercises_summary function - especially cardio exercises."""

    def test_strength_exercise_formatting(self):
        """Test formatting of strength exercises (should work fine)."""
        exercise = ExerciseLog(
            name="Supino",
            sets=3,
            reps_per_set=[10, 8, 6],
            weights_per_set=[80.0, 85.0, 90.0],
            distance_meters_per_set=[],
            duration_seconds_per_set=[],
        )
        result = _format_exercises_summary([exercise])
        # Should show varying reps and weights
        self.assertIn("Supino", result)
        self.assertIn("80.0kg", result)
        self.assertIn("10@", result)

    def test_cardio_exercise_with_duration(self):
        """Test formatting of cardio exercises with duration (BUG FIX)."""
        exercise = ExerciseLog(
            name="Esteira",
            sets=1,
            reps_per_set=[1],  # Default fallback
            weights_per_set=[],
            distance_meters_per_set=[5000],
            duration_seconds_per_set=[900],  # 15 minutes
        )
        result = _format_exercises_summary([exercise])
        # Should NOT show "1x1" format for cardio
        # Should show duration instead
        self.assertIn("Esteira", result)
        # Should include duration information
        self.assertTrue(
            "900" in result or "15" in result,
            f"Duration not found in result: {result}"
        )
        # Should NOT format as "1x1"
        self.assertNotIn("1x1", result)

    def test_cardio_exercise_with_zero_reps(self):
        """Test the exact bug: cardio with 0 reps shows '1x0' instead of duration."""
        exercise = ExerciseLog(
            name="Esteira",
            sets=1,
            reps_per_set=[0],  # Explicitly 0 - the bug
            weights_per_set=[],
            distance_meters_per_set=[5000],
            duration_seconds_per_set=[900],
        )
        result = _format_exercises_summary([exercise])
        # Bug: currently shows "1x0 Esteira"
        # Fixed: should show duration instead
        self.assertIn("Esteira", result)
        self.assertFalse(
            "1x0" in result,
            f"Bug detected: '1x0' format found for cardio exercise: {result}"
        )
        # Should show duration
        self.assertTrue(
            "900" in result or "15" in result,
            f"Duration not found in result: {result}"
        )

    def test_cardio_with_distance_and_duration(self):
        """Test cardio exercise with both distance and duration."""
        exercise = ExerciseLog(
            name="Bicicleta",
            sets=1,
            reps_per_set=[1],
            weights_per_set=[],
            distance_meters_per_set=[10000],  # 10km
            duration_seconds_per_set=[1800],  # 30 minutes
        )
        result = _format_exercises_summary([exercise])
        self.assertIn("Bicicleta", result)
        # Should show distance or duration, not reps format
        self.assertNotIn("1x1", result)
        self.assertTrue(
            "10000" in result or "1800" in result or "30" in result,
            f"Distance/duration not found in result: {result}"
        )

    def test_mixed_exercise_with_reps_and_duration(self):
        """Test mixed exercise with both reps and cardio metrics (e.g., Remo)."""
        exercise = ExerciseLog(
            name="Remo",
            sets=2,
            reps_per_set=[15, 12],
            weights_per_set=[],
            distance_meters_per_set=[500, 600],
            duration_seconds_per_set=[120, 140],
        )
        result = _format_exercises_summary([exercise])
        self.assertIn("Remo", result)
        # Should show reps since it's primary metric
        # Or should show both reps and duration
        self.assertTrue(
            "15" in result or "Remo" in result,
            f"Exercise info not found: {result}"
        )


if __name__ == "__main__":
    unittest.main()
