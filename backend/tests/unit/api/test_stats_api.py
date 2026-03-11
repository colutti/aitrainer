"""
Unit tests for the workout statistics API endpoints.
"""

import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_stats import WorkoutStats, VolumeStat, PersonalRecord

class TestStatsApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides = {}

    def test_get_workout_stats_success(self):
        """Test successful retrieval of workout statistics."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        expected_stats = WorkoutStats(
            current_streak_weeks=2,
            weekly_frequency=[True, False, True, False, True, False, False],
            weekly_volume=[VolumeStat(category="Pernas", volume=1000.0)],
            recent_prs=[
                PersonalRecord(
                    exercise_name="Supino",
                    weight=100.0,
                    reps=1,
                    date=datetime(2023, 1, 1),
                    workout_id="123",
                )
            ],
            total_workouts=10,
            last_workout=None,
        )

        mock_db.get_workout_stats.return_value = expected_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/workout/stats", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_streak_weeks"], 2)
        self.assertEqual(data["weekly_volume"][0]["category"], "Pernas")

    def test_get_workout_stats_unauthenticated(self):
        """Test stats retrieval without authentication."""
        from fastapi import HTTPException, status
        def mock_unauthenticated():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        app.dependency_overrides[verify_token] = mock_unauthenticated

        response = self.client.get("/workout/stats")
        self.assertEqual(response.status_code, 401)

    def test_get_workout_stats_error(self):
        """Test error handling when fetching stats fails."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_stats.side_effect = Exception("DB Error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/workout/stats", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve workout stats")

if __name__ == "__main__":
    unittest.main()
