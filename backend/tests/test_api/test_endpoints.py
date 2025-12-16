
"""
This module contains unit tests for the API endpoints.
"""
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.user_profile import UserProfile


class TestEndpoints(unittest.TestCase):
    """
    Tests for the API endpoints.
    """
    # pylint: disable=invalid-name
    def setUp(self):
        """
        Set up the test client before each test.
        """
        self.client = TestClient(app)

    @patch("src.api.endpoints.user.user_login")
    def test_login_success(self, mock_user_login):
        """
        Test successful user login.
        """
        # Arrange
        mock_user_login.return_value = "test_token"

        # Act
        response = self.client.post("/login",
                                    json={"email": "test@test.com",
                                          "password": "password"})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"token": "test_token"})

    @patch("src.api.endpoints.user.user_login")
    def test_login_failure(self, mock_user_login):
        """
        Test failed user login with invalid credentials.
        """
        # Arrange
        mock_user_login.side_effect = ValueError("Invalid credentials")

        # Act
        response = self.client.post("/login",
                                    json={"email": "test@test.com",
                                          "password": "password"})

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Invalid credentials"})

    def test_get_profile_success(self):
        """
        Test successful retrieval of user profile.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_user_profile.return_value = UserProfile(
            email="test@test.com",
            gender="Masculino",
            age=25,
            weight=70,
            height=175,
            goal="Gain muscle"
        )
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get("/profile",
                                   headers={"Authorization": "Bearer test_token"})

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "test@test.com")

        # Clean up
        app.dependency_overrides = {}

    def test_get_profile_not_found(self):
        """
        Test retrieval of non-existent user profile.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_user_profile.return_value = None
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get("/profile",
                                   headers={"Authorization": "Bearer test_token"})

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "User profile not found"})

        # Clean up
        app.dependency_overrides = {}


if __name__ == "__main__":
    unittest.main()
