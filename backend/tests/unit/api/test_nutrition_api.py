"""
Unit tests for the nutrition API endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from io import BytesIO

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.api.models.nutrition_log import NutritionWithId
from src.api.models.nutrition_stats import NutritionStats, DailyMacros
from src.api.models.import_result import ImportResult

class TestNutritionApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides = {}

    def test_list_nutrition_success(self):
        """Test successful retrieval of paginated nutrition logs."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

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
        self.assertEqual(data["logs"][0]["calories"], 2000)

    def test_get_nutrition_stats_success(self):
        """Test retrieving nutrition statistics."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        today_log = NutritionWithId(
            id="1",
            user_email="test@test.com",
            date=datetime(2024, 1, 5),
            calories=2000,
            protein_grams=150.0,
            carbs_grams=200.0,
            fat_grams=60.0,
            notes="Today",
            source="manual"
        )

        mock_stats = NutritionStats(
            today=today_log,
            weekly_adherence=[True] * 7,
            last_7_days=[DailyMacros(date=datetime(2024,1,5), calories=2000, protein=150, carbs=200, fat=60)],
            avg_daily_calories=2000.0,
            avg_daily_calories_14_days=2000.0,
            avg_protein=150.0,
            total_logs=10,
            tdee=2500,
            daily_target=2000,
            macro_targets={},
            stability_score=100
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/stats",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["avg_daily_calories"], 2000.0)

    def test_get_today_nutrition_success(self):
        """Test retrieving today's nutrition log."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        today_log = NutritionWithId(
            id="1",
            user_email="test@test.com",
            date=datetime(2024, 1, 5),
            calories=2000,
            protein_grams=150.0,
            carbs_grams=200.0,
            fat_grams=60.0,
            notes="Today",
            source="manual"
        )

        mock_stats = NutritionStats(
            today=today_log,
            weekly_adherence=[False] * 7,
            last_7_days=[],
            avg_daily_calories=0.0,
            avg_daily_calories_14_days=0.0,
            avg_protein=0.0,
            total_logs=0,
            tdee=0,
            daily_target=0,
            macro_targets={},
            stability_score=0
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/today",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["calories"], 2000)

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

    def test_import_nutrition_success(self):
        """Test successful MyFitnessPal import."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        with patch('src.api.endpoints.nutrition.import_nutrition_from_csv') as mock_import:
            mock_import.return_value = ImportResult(created=5, updated=0, errors=0, total_days=5)
            csv_content = b"Date,Calories,Protein,Carbs,Fat\n2024-01-29,2000,150,250,70"

            response = self.client.post(
                "/nutrition/import/myfitnesspal",
                files={"file": ("test.csv", BytesIO(csv_content), "text/csv")},
                headers={"Authorization": "Bearer token"}
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["created"], 5)

if __name__ == "__main__":
    unittest.main()
