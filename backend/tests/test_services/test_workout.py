"""
Unit tests for workout tracking functionality.
"""

import unittest
from unittest.mock import MagicMock
from datetime import datetime

from src.api.models.workout_log import ExerciseLog, WorkoutLog
from src.services.workout_tools import create_save_workout_tool, create_get_workouts_tool


class TestWorkoutLogModels(unittest.TestCase):
    """Tests for WorkoutLog and ExerciseLog Pydantic models."""

    def test_exercise_log_creation(self):
        """Test creating an ExerciseLog with valid data."""
        exercise = ExerciseLog(
            name="Supino Reto",
            sets=3,
            reps=12,
            weight_kg=80.5
        )
        self.assertEqual(exercise.name, "Supino Reto")
        self.assertEqual(exercise.sets, 3)
        self.assertEqual(exercise.reps, 12)
        self.assertEqual(exercise.weight_kg, 80.5)

    def test_exercise_log_without_weight(self):
        """Test creating an ExerciseLog without weight (optional field)."""
        exercise = ExerciseLog(
            name="Flexão",
            sets=4,
            reps=15
        )
        self.assertIsNone(exercise.weight_kg)

    def test_workout_log_creation(self):
        """Test creating a complete WorkoutLog."""
        exercises = [
            ExerciseLog(name="Agachamento", sets=4, reps=10, weight_kg=100),
            ExerciseLog(name="Leg Press", sets=3, reps=12, weight_kg=200),
        ]
        workout = WorkoutLog(
            user_email="test@example.com",
            workout_type="Legs",
            exercises=exercises,
            duration_minutes=45
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
            exercises=[ExerciseLog(name="Supino", sets=3, reps=10, weight_kg=60)],
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

    def test_save_workout_tool_execution(self):
        """Test executing the save_workout tool."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")
        
        result = tool.invoke({
            "workout_type": "Legs",
            "exercises": [
                {"name": "Agachamento", "sets": 4, "reps": 10, "weight_kg": 100}
            ],
            "duration_minutes": 45
        })
        
        self.assertIn("sucesso", result.lower())
        self.mock_db.save_workout_log.assert_called_once()
        
        # Verify the workout was created correctly
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        self.assertEqual(saved_workout.user_email, "user@test.com")
        self.assertEqual(saved_workout.workout_type, "Legs")
        self.assertEqual(len(saved_workout.exercises), 1)

    def test_save_workout_tool_with_multiple_exercises(self):
        """Test saving a workout with multiple exercises."""
        tool = create_save_workout_tool(self.mock_db, "athlete@test.com")
        
        result = tool.invoke({
            "workout_type": "Push",
            "exercises": [
                {"name": "Supino Reto", "sets": 4, "reps": 8, "weight_kg": 80},
                {"name": "Supino Inclinado", "sets": 3, "reps": 10, "weight_kg": 60},
                {"name": "Tríceps Corda", "sets": 3, "reps": 12, "weight_kg": 25},
            ],
            "duration_minutes": 60
        })
        
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        self.assertEqual(len(saved_workout.exercises), 3)
        self.assertEqual(saved_workout.duration_minutes, 60)

    def test_save_workout_tool_without_duration(self):
        """Test saving a workout without duration (optional field)."""
        tool = create_save_workout_tool(self.mock_db, "user@test.com")
        
        tool.invoke({
            "workout_type": "Upper",
            "exercises": [
                {"name": "Flexão", "sets": 3, "reps": 15}
            ]
        })
        
        saved_workout = self.mock_db.save_workout_log.call_args[0][0]
        self.assertIsNone(saved_workout.duration_minutes)

    def test_save_workout_tool_error_handling(self):
        """Test that errors are handled gracefully."""
        self.mock_db.save_workout_log.side_effect = Exception("Database error")
        tool = create_save_workout_tool(self.mock_db, "user@test.com")
        
        result = tool.invoke({
            "workout_type": "Legs",
            "exercises": [{"name": "Test", "sets": 1, "reps": 1}]
        })
        
        self.assertIn("erro", result.lower())


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
                    ExerciseLog(name="Supino", sets=4, reps=10, weight_kg=80),
                    ExerciseLog(name="Tríceps", sets=3, reps=12, weight_kg=25),
                ],
                duration_minutes=45
            ),
            WorkoutLog(
                user_email="user@test.com",
                date=datetime(2025, 12, 20, 10, 0),
                workout_type="Legs",
                exercises=[
                    ExerciseLog(name="Agachamento", sets=4, reps=10, weight_kg=100),
                ],
                duration_minutes=60
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
        self.assertIn("45min", result)

    def test_get_workouts_with_limit(self):
        """Test that limit parameter is passed correctly."""
        self.mock_db.get_workout_logs.return_value = [self.sample_workouts[0]]
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")
        
        tool.invoke({"limit": 1})
        
        self.mock_db.get_workout_logs.assert_called_once_with("user@test.com", limit=1)

    def test_get_workouts_empty_history(self):
        """Test message when no workouts found."""
        self.mock_db.get_workout_logs.return_value = []
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")
        
        result = tool.invoke({"limit": 5})
        
        self.assertIn("Nenhum treino registrado", result)

    def test_get_workouts_error_handling(self):
        """Test that errors are handled gracefully."""
        self.mock_db.get_workout_logs.side_effect = Exception("Database error")
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")
        
        result = tool.invoke({"limit": 5})
        
        self.assertIn("Erro", result)

    def test_get_workouts_without_duration(self):
        """Test formatting when workout has no duration."""
        workout_no_duration = WorkoutLog(
            user_email="user@test.com",
            date=datetime(2025, 12, 21, 14, 30),
            workout_type="Upper",
            exercises=[ExerciseLog(name="Flexão", sets=3, reps=15)],
            duration_minutes=None
        )
        self.mock_db.get_workout_logs.return_value = [workout_no_duration]
        tool = create_get_workouts_tool(self.mock_db, "user@test.com")
        
        result = tool.invoke({"limit": 5})
        
        # Should not contain "min" when no duration
        self.assertIn("Upper", result)
        self.assertNotIn("min)", result)


if __name__ == "__main__":
    unittest.main()
