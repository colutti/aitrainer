"""
Unit tests for the weight API endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import date, timedelta
from io import BytesIO

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.api.models.weight_log import WeightLog
from src.api.models.import_result import ImportResult

def mock_get_current_user():
    return "test@example.com"

class TestWeightApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides = {}

    def test_log_weight_success(self):
        """Test successful weight logging."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_brain = MagicMock()
        mock_db = MagicMock()
        mock_db.weight.save_log.return_value = ("123", True)
        mock_db.weight.get_logs.return_value = []

        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        payload = {
            "date": str(date.today()),
            "weight_kg": 75.5,
            "notes": "Morning weight",
        }

        response = self.client.post(
            "/weight", json=payload, headers={"Authorization": "Bearer test_token"}
        )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data["message"], "Weight logged successfully")
        self.assertEqual(res_data["id"], "123")
        self.assertTrue(res_data["is_new"])
        self.assertIn("trend_weight", res_data)

    def test_log_weight_with_ema_trend(self):
        """Test that EMA trend is calculated correctly."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_db = MagicMock()

        prev_log = WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=1),
            weight_kg=76.0,
            trend_weight=75.8
        )
        mock_db.weight.get_logs.return_value = [prev_log]
        mock_db.weight.save_log.return_value = ("456", False)

        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        payload = {
            "date": str(date.today()),
            "weight_kg": 75.5,
        }

        response = self.client.post(
            "/weight", json=payload, headers={"Authorization": "Bearer test_token"}
        )

        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertIsNotNone(res_data["trend_weight"])

    def test_get_weight_logs_success(self):
        """Test successful retrieval of weight logs."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_db = MagicMock()
        
        logs = [
            {"id": "id_1", "user_email": "test@example.com", "date": str(date.today()), "weight_kg": 75.5},
            {"id": "id_2", "user_email": "test@example.com", "date": str(date.today() - timedelta(days=1)), "weight_kg": 76.0},
        ]
        mock_db.get_weight_paginated.return_value = (logs, 2)
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        response = self.client.get("/weight", headers={"Authorization": "Bearer test_token"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["logs"]), 2)
        self.assertEqual(data["total"], 2)

    def test_delete_weight_log_success(self):
        """Test successful deletion of weight log."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_brain = MagicMock()
        mock_brain.database.delete_weight_log.return_value = True
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        date_str = str(date.today())
        response = self.client.delete(
            f"/weight/{date_str}", headers={"Authorization": "Bearer test_token"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["deleted"])

    def test_get_body_composition_stats_success(self):
        """Test retrieving body composition stats."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_brain = MagicMock()

        logs = [
            WeightLog(user_email="test@example.com", date=date.today() - timedelta(days=i), weight_kg=75.0 + i*0.1)
            for i in range(5)
        ]
        mock_brain.database.get_weight_logs.return_value = logs
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        response = self.client.get("/weight/stats", headers={"Authorization": "Bearer test_token"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("latest", data)
        self.assertIn("weight_trend", data)

    def test_import_zepp_life_success(self):
        """Test successful import from Zepp Life."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        mock_db = MagicMock()
        app.dependency_overrides[get_mongo_database] = lambda: mock_db

        with patch("src.api.endpoints.weight.import_zepp_life_data") as mock_import:
            mock_import.return_value = ImportResult(created=10, updated=2, errors=0, total_days=30)
            csv_content = b"Date,Weight,BodyFat\n2024-01-29,75.5,22.0"

            response = self.client.post(
                "/weight/import/zepp-life",
                files={"file": ("zepp.csv", BytesIO(csv_content), "text/csv")},
                headers={"Authorization": "Bearer test_token"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["created"], 10)
            self.assertEqual(data["updated"], 2)

    def test_import_zepp_life_invalid_file(self):
        """Test importing file with invalid extension."""
        app.dependency_overrides[verify_token] = mock_get_current_user
        response = self.client.post(
            "/weight/import/zepp-life",
            files={"file": ("data.txt", BytesIO(b"data"), "text/plain")},
            headers={"Authorization": "Bearer test_token"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("CSV", response.json()["detail"])

if __name__ == "__main__":
    unittest.main()
