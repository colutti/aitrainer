import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from datetime import datetime


class TestNutritionEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_nutrition_success(self):
        """Test successful retrieval of paginated nutrition logs."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        # Mock DB response
        mock_logs = [
            {
                "_id": "1",
                "id": "1",
                "user_email": "test@test.com",
                "date": datetime(2024, 1, 1),
                "calories": 2000,
                "protein_grams": 150.0,
                "carbs_grams": 200.0,
                "fat_grams": 60.0,
                "source": "manual",
            }
        ]
        mock_db.get_nutrition_paginated.return_value = (mock_logs, 1)

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/list?page=1&page_size=10",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["logs"]), 1)
        self.assertEqual(data["logs"][0]["calories"], 2000)

        mock_db.get_nutrition_paginated.assert_called_with(
            user_email="test@test.com", page=1, page_size=10, days=None
        )
        app.dependency_overrides = {}

    def test_delete_nutrition_success(self):
        """Test successful deletion of a nutrition log."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_by_id.return_value = {"user_email": "test@test.com"}
        mock_db.delete_nutrition_log.return_value = True
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.delete(
            "/nutrition/log123", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Nutrition log deleted successfully")
        mock_db.delete_nutrition_log.assert_called_with("log123")
        app.dependency_overrides = {}

    def test_delete_nutrition_not_found(self):
        """Test deleting a non-existent nutrition log."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_by_id.return_value = None
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.delete(
            "/nutrition/nonexistent", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Nutrition log not found")
        app.dependency_overrides = {}

    def test_delete_nutrition_unauthorized(self):
        """Test deleting a nutrition log owned by another user."""
        app.dependency_overrides[verify_token] = lambda: "attacker@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_by_id.return_value = {"user_email": "victim@test.com"}
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.delete(
            "/nutrition/log123", headers={"Authorization": "Bearer token"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Not authorized to delete this nutrition log")
        app.dependency_overrides = {}
