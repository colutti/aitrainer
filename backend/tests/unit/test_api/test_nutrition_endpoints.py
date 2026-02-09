import unittest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from datetime import datetime
import io


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

    def test_list_nutrition_with_days_filter(self):
        """Test listing nutrition logs with days filter."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_logs = [
            {
                "_id": "1",
                "id": "1",
                "user_email": "test@test.com",
                "date": datetime(2024, 1, 5),
                "calories": 1900,
                "protein_grams": 145.0,
                "carbs_grams": 190.0,
                "fat_grams": 58.0,
                "source": "manual",
            }
        ]
        mock_db.get_nutrition_paginated.return_value = (mock_logs, 1)
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/list?page=1&page_size=10&days=7",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 1)
        mock_db.get_nutrition_paginated.assert_called_with(
            user_email="test@test.com", page=1, page_size=10, days=7
        )
        app.dependency_overrides = {}

    def test_list_nutrition_pagination_calculation(self):
        """Test correct pagination calculation with multiple pages."""
        from datetime import timedelta

        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        base_date = datetime(2024, 1, 5)
        mock_logs = [
            {
                "_id": str(i),
                "id": str(i),
                "user_email": "test@test.com",
                "date": base_date - timedelta(days=i),
                "calories": 2000,
                "protein_grams": 150.0,
                "carbs_grams": 200.0,
                "fat_grams": 60.0,
                "source": "manual",
            }
            for i in range(10)
        ]
        mock_db.get_nutrition_paginated.return_value = (mock_logs, 25)  # 25 total items, 10 per page
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/list?page=1&page_size=10",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 25)
        self.assertEqual(data["total_pages"], 3)  # ceil(25/10)
        app.dependency_overrides = {}

    def test_list_nutrition_empty_result(self):
        """Test listing when no nutrition logs exist."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_paginated.return_value = ([], 0)
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/list?page=1&page_size=10",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(data["total_pages"], 0)
        self.assertEqual(len(data["logs"]), 0)
        app.dependency_overrides = {}

    def test_get_nutrition_stats_success(self):
        """Test retrieving nutrition statistics."""
        from src.api.models.nutrition_stats import NutritionStats, DailyMacros
        from src.api.models.nutrition_log import NutritionWithId
        from datetime import timedelta

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
            source="manual",
        )

        base_date = datetime(2024, 1, 5)
        daily_macros = [
            DailyMacros(date=base_date - timedelta(days=i), calories=2000, protein=150.0, carbs=200.0, fat=60.0)
            for i in range(7)
        ]

        mock_stats = NutritionStats(
            today=today_log,
            weekly_adherence=[True] * 7,
            last_7_days=daily_macros,
            avg_daily_calories=2000.0,
            avg_protein=150.0,
            total_logs=10,
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/stats",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["avg_daily_calories"], 2000.0)
        mock_db.get_nutrition_stats.assert_called_with("test@test.com")
        app.dependency_overrides = {}

    def test_get_nutrition_stats_empty(self):
        """Test retrieving stats when no nutrition logs exist."""
        from src.api.models.nutrition_stats import NutritionStats

        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        mock_stats = NutritionStats(
            today=None,
            weekly_adherence=[False] * 7,
            last_7_days=[],
            avg_daily_calories=0.0,
            avg_protein=0.0,
            total_logs=0,
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/stats",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data["today"])
        self.assertEqual(data["total_logs"], 0)
        app.dependency_overrides = {}

    def test_get_today_nutrition_success(self):
        """Test retrieving today's nutrition log."""
        from src.api.models.nutrition_stats import NutritionStats
        from src.api.models.nutrition_log import NutritionWithId

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
            source="manual",
        )

        mock_stats = NutritionStats(
            today=today_log,
            weekly_adherence=[False] * 7,
            last_7_days=[],
            avg_daily_calories=0.0,
            avg_protein=0.0,
            total_logs=0,
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/today",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["calories"], 2000)
        app.dependency_overrides = {}

    def test_get_today_nutrition_none(self):
        """Test retrieving today's nutrition when no entry exists."""
        from src.api.models.nutrition_stats import NutritionStats

        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()

        mock_stats = NutritionStats(
            today=None,
            weekly_adherence=[False] * 7,
            last_7_days=[],
            avg_daily_calories=0.0,
            avg_protein=0.0,
            total_logs=0,
        )
        mock_db.get_nutrition_stats.return_value = mock_stats
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/today",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json())
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

    def test_import_nutrition_invalid_extension(self):
        """Test importing file with invalid extension."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        # Create a fake .txt file
        response = self.client.post(
            "/nutrition/import/myfitnesspal",
            files={"file": ("data.txt", io.BytesIO(b"data"), "text/plain")},
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "O arquivo deve ser um CSV.")
        app.dependency_overrides = {}

    def test_import_nutrition_validation_error(self):
        """Test importing CSV with validation error."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        from unittest.mock import patch

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        csv_content = b"invalid,csv,format"

        with patch('src.api.endpoints.nutrition.import_nutrition_from_csv') as mock_import:
            mock_import.side_effect = ValueError("Missing required columns")

            response = self.client.post(
                "/nutrition/import/myfitnesspal",
                files={"file": ("data.csv", io.BytesIO(csv_content), "text/csv")},
                headers={"Authorization": "Bearer token"},
            )

            self.assertEqual(response.status_code, 400)
            self.assertIn("Missing required columns", response.json()["detail"])
        app.dependency_overrides = {}

    def test_list_nutrition_db_error(self):
        """Test handling database error during list."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_paginated.side_effect = Exception("DB connection error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/list?page=1&page_size=10",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve nutrition logs")
        app.dependency_overrides = {}

    def test_get_nutrition_stats_db_error(self):
        """Test handling database error during stats retrieval."""
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_db = MagicMock()
        mock_db.get_nutrition_stats.side_effect = Exception("DB connection error")
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get(
            "/nutrition/stats",
            headers={"Authorization": "Bearer token"},
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"], "Failed to retrieve nutrition stats")
        app.dependency_overrides = {}
