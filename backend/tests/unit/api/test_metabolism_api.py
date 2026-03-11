"""
Unit tests for the metabolism API endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_mongo_database

class TestMetabolismApi(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides = {}

    def test_get_metabolism_summary_success(self):
        """Test successful retrieval of metabolism summary."""
        app.dependency_overrides[verify_token] = lambda: "test@example.com"
        mock_db = MagicMock()

        with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.calculate_tdee.return_value = {
                "tdee": 2500,
                "confidence": "high",
                "trend": "stable",
                "weekly_logs": 7,
                "data_points": 30,
            }
            mock_service_class.return_value = mock_service
            app.dependency_overrides[get_mongo_database] = lambda: mock_db

            response = self.client.get(
                "/metabolism/summary",
                headers={"Authorization": "Bearer test_token"}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["tdee"], 2500)
            self.assertEqual(data["confidence"], "high")

    def test_get_metabolism_summary_unauthorized(self):
        """Test metabolism summary without authentication."""
        response = self.client.get("/metabolism/summary")
        self.assertEqual(response.status_code, 401)

    def test_get_metabolism_summary_custom_weeks(self):
        """Test metabolism summary with custom lookback period."""
        app.dependency_overrides[verify_token] = lambda: "test@example.com"
        mock_db = MagicMock()

        with patch("src.api.endpoints.metabolism.AdaptiveTDEEService") as mock_service_class:
            mock_service = MagicMock()
            mock_service.calculate_tdee.return_value = {"tdee": 2300, "confidence": "medium"}
            mock_service_class.return_value = mock_service
            app.dependency_overrides[get_mongo_database] = lambda: mock_db

            response = self.client.get(
                "/metabolism/summary?weeks=8",
                headers={"Authorization": "Bearer test_token"}
            )

            self.assertEqual(response.status_code, 200)
            mock_service.calculate_tdee.assert_called_once_with("test@example.com", lookback_weeks=8)

if __name__ == "__main__":
    unittest.main()
