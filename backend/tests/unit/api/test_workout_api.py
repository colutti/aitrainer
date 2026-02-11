"""
Unit tests for the workout API endpoints.
"""

import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database

class TestWorkoutApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides = {}

    def test_list_workouts_success(self):
        """Test successful retrieval of paginated workouts."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        mock_workouts = [
            {
                "_id": "1",
                "id": "1",
                "user_email": "test@test.com",
                "date": datetime(2024, 1, 1),
                "workout_type": "Push",
                "exercises": [],
                "duration_minutes": 60,
            }
        ]
        mock_db.get_workouts_paginated.return_value = (mock_workouts, 1)
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/workout/list?page=1&page_size=10",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["workouts"][0]["workout_type"], "Push")

    def test_get_types_success(self):
        """Test retrieval of workout types."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_types.return_value = ["Push", "Pull", "Legs"]
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/workout/types", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["Push", "Pull", "Legs"])

    def test_delete_workout_success(self):
        """Test successful deletion of a workout log."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_by_id.return_value = {"user_email": "test@test.com"}
        mock_db.delete_workout_log.return_value = True
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.delete(
            "/workout/workout123", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Workout deleted successfully")

    def test_delete_workout_unauthorized(self):
        """Test deleting a workout owned by another user."""
        app.dependency_overrides[verify_token] = lambda: "attacker@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_by_id.return_value = {"user_email": "victim@test.com"}
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.delete(
            "/workout/workout123", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
