import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.workout_log import WorkoutListResponse, WorkoutWithId
from datetime import datetime

class TestWorkoutEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_workouts_success(self):
        """Test successful retrieval of paginated workouts."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        
        # Mock DB response
        mock_workouts = [
            {
                "_id": "1",
                "id": "1",
                "user_email": "test@test.com",
                "date": datetime(2024, 1, 1),
                "workout_type": "Push",
                "exercises": [],
                "duration_minutes": 60
            }
        ]
        # get_workouts_paginated returns (workouts, total_count)
        mock_db.get_workouts_paginated.return_value = (mock_workouts, 1)
        
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        # Act
        response = self.client.get("/workout/list?page=1&page_size=10", headers={"Authorization": "Bearer token"})

        # Assert
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["workouts"]), 1)
        self.assertEqual(data["workouts"][0]["workout_type"], "Push")
        
        # Verify call arguments (including filter=None defaults)
        mock_db.get_workouts_paginated.assert_called_with(
            user_email="test@test.com",
            page=1,
            page_size=10,
            workout_type=None
        )

        app.dependency_overrides = {}

    def test_list_workouts_with_filter(self):
        """Test listing workouts with type filter."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workouts_paginated.return_value = ([], 0)
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        self.client.get("/workout/list?workout_type=Pull", headers={"Authorization": "Bearer token"})

        mock_db.get_workouts_paginated.assert_called_with(
            user_email="test@test.com",
            page=1,
            page_size=10,
            workout_type="Pull"
        )
        app.dependency_overrides = {}

    def test_list_workouts_error(self):
        """Test error handling in list workouts."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workouts_paginated.side_effect = Exception("DB Error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get("/workout/list", headers={"Authorization": "Bearer token"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve workouts")
        app.dependency_overrides = {}

    def test_get_types_success(self):
        """Test retrieval of workout types."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_types.return_value = ["Push", "Pull", "Legs"]
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get("/workout/types", headers={"Authorization": "Bearer token"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), ["Push", "Pull", "Legs"])
        app.dependency_overrides = {}

    def test_get_types_error(self):
        """Test error handling for workout types."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_workout_types.side_effect = Exception("DB Error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get("/workout/types", headers={"Authorization": "Bearer token"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve workout types")
        app.dependency_overrides = {}
