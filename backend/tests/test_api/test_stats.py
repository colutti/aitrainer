import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_stats import WorkoutStats, VolumeStat, PersonalRecord
from datetime import datetime

class TestStatsEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_workout_stats_success(self):
        # Arrange
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
                    workout_id="123"
                )
            ],
            total_workouts=10,
            last_workout=None
        )
        
        mock_db.get_workout_stats.return_value = expected_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        # Act
        response = self.client.get("/workout/stats", headers={"Authorization": "Bearer token"})
        
        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_streak_weeks"], 2)
        self.assertEqual(data["weekly_volume"][0]["category"], "Pernas")
        self.assertEqual(data["recent_prs"][0]["exercise_name"], "Supino")
        
        # Clean up
        app.dependency_overrides = {}

    def test_get_workout_stats_unauthenticated(self):
        # Arrange
        # No override for verify_token means it relies on real/mock implementation that might fail 
        # or we explicitly mock it to raise exception if not overridden.
        # But verify_token usually raises 401 if fails.
        # In test_endpoints.py, they override it to raise 401.
        
        from fastapi import HTTPException, status
        def mock_unauthenticated():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
            
        app.dependency_overrides[verify_token] = mock_unauthenticated

        # Act
        response = self.client.get("/workout/stats")

        # Assert
        self.assertEqual(response.status_code, 401)
        app.dependency_overrides = {}

    def test_get_workout_stats_error(self):
        """Test error handling when fetching stats fails."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_stats.side_effect = Exception("DB Error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get("/workout/stats", headers={"Authorization": "Bearer token"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve workout stats")
        app.dependency_overrides = {}


if __name__ == "__main__":
    unittest.main()
