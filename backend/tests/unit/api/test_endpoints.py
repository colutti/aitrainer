"""
This module contains unit tests for the API endpoints.
"""

import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.api.models.sender import Sender
from src.api.models.chat_history import ChatHistory
from src.api.models.message import MessageRequest
from src.api.models.trainer_profile import TrainerProfile, TrainerProfileInput


def mock_unauthenticated_user():
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )


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
        response = self.client.post(
            "/user/login", json={"email": "test@test.com", "password": "password"}
        )

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
        response = self.client.post(
            "/user/login", json={"email": "test@test.com", "password": "password"}
        )

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
            weight=70.0,
            height=175,
            goal="Gain muscle",
            goal_type="maintain",
        )
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get(
            "/user/profile", headers={"Authorization": "Bearer test_token"}
        )

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
        response = self.client.get(
            "/user/profile", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"detail": "User profile not found"})

        # Clean up
        app.dependency_overrides = {}

    def test_update_profile_success(self):
        """
        Test successful update of user profile.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        mock_brain.save_user_profile.return_value = (
            None  # Assuming save_user_profile returns None
        )
        profile_data = UserProfileInput(
            gender="Masculino",
            age=30,
            weight=75,
            height=180,
            goal="Lose weight",
            goal_type="lose",
        ).model_dump()

        # Act
        response = self.client.post(
            "/user/update_profile",
            headers={"Authorization": "Bearer test_token"},
            json=profile_data,
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Profile updated successfully"})
        mock_brain.save_user_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_update_profile_resets_coaching_data_when_goal_changes(self):
        """
        BUG: Quando weekly_rate ou goal_type muda, tdee_last_check_in/tdee_last_target
        devem ser resetados para forçar recálculo com a nova meta.

        Sem o reset, se check_in=hoje e prev_target=TDEE, o sistema retorna TDEE
        mesmo com nova meta diferente.
        """
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Existing profile has old goal (0.25) and coaching data stuck at TDEE
        existing_profile = UserProfile(
            email="test@test.com",
            password_hash="hash",
            gender="Masculino",
            age=30,
            weight=80.0,
            height=180,
            goal_type="lose",
            weekly_rate=0.25,
            tdee_last_target=2508,
            tdee_last_check_in="2026-02-18",  # today - blocks recalculation
        )
        mock_brain.get_user_profile.return_value = existing_profile

        # User changes weekly_rate to 0.5 (all required fields must be sent)
        response = self.client.post(
            "/user/update_profile",
            headers={"Authorization": "Bearer test_token"},
            json={
                "gender": "Masculino",
                "age": 30,
                "weight": 80.0,
                "height": 180,
                "goal_type": "lose",
                "weekly_rate": 0.5,  # changed from 0.25
            },
        )

        self.assertEqual(response.status_code, 200)
        # Must reset coaching check-in so next calculate_tdee uses new goal
        mock_brain.update_user_profile_fields.assert_called_once_with(
            "test@test.com",
            {"tdee_last_check_in": None, "tdee_last_target": None},
        )
        app.dependency_overrides = {}

    def test_update_profile_does_not_reset_coaching_data_when_goal_unchanged(self):
        """
        Quando goal_type e weekly_rate NÃO mudam, não deve resetar coaching data.
        Isso evita interromper check-ins normais por updates de outros campos.
        """
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        existing_profile = UserProfile(
            email="test@test.com",
            password_hash="hash",
            gender="Masculino",
            age=30,
            weight=80.0,
            height=180,
            goal_type="lose",
            weekly_rate=0.25,
            tdee_last_target=2233,
            tdee_last_check_in="2026-02-18",
        )
        mock_brain.get_user_profile.return_value = existing_profile

        # User changes only weight (not goal) - all required fields sent, goal unchanged
        response = self.client.post(
            "/user/update_profile",
            headers={"Authorization": "Bearer test_token"},
            json={
                "gender": "Masculino",
                "age": 30,
                "weight": 79.0,  # changed
                "height": 180,
                "goal_type": "lose",  # same
                "weekly_rate": 0.25,  # same
            },
        )

        self.assertEqual(response.status_code, 200)
        # Should NOT reset coaching data
        mock_brain.update_user_profile_fields.assert_not_called()
        app.dependency_overrides = {}

    def test_update_profile_unauthenticated(self):
        """
        Test update of user profile without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user
        profile_data = UserProfileInput(
            gender="Masculino",
            age=30,
            weight=75,
            height=180,
            goal="Lose weight",
            goal_type="lose",
        ).model_dump()

        # Act
        response = self.client.post("/user/update_profile", json=profile_data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}

    @patch("src.api.endpoints.user.user_logout")
    def test_logout_success_post(self, mock_user_logout):
        """
        Test successful user logout via POST.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        token_to_logout = "test_token"

        # Act
        response = self.client.post(
            "/user/logout", headers={"Authorization": f"Bearer {token_to_logout}"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Logged out successfully"})
        mock_user_logout.assert_called_once_with(token_to_logout)
        app.dependency_overrides = {}

    def test_logout_get_not_allowed(self):
        """
        Test that GET logout returns 405 Method Not Allowed.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"

        # Act
        response = self.client.get(
            "/user/logout", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 405)
        app.dependency_overrides = {}

    def test_logout_unauthenticated(self):
        """
        Test user logout without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user

        # Act
        response = self.client.post("/user/logout")

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}

    def test_get_history_success_empty(self):
        """
        Test successful retrieval of empty chat history.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_chat_history.return_value = []
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get(
            "/message/history", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        app.dependency_overrides = {}

    def test_get_history_success_with_messages(self):
        """
        Test successful retrieval of chat history with messages.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_chat_history.return_value = [
            ChatHistory(
                text="Hello", sender=Sender.STUDENT, timestamp="2023-01-01T12:00:00"
            ),
            ChatHistory(
                text="Hi there!", sender=Sender.TRAINER, timestamp="2023-01-01T12:00:01"
            ),
        ]
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get(
            "/message/history", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)
        self.assertEqual(response.json()[0]["text"], "Hello")
        app.dependency_overrides = {}

    def test_get_history_unauthenticated(self):
        """
        Test retrieval of chat history without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user

        # Act
        response = self.client.get("/message/history")

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}

    def test_message_ai_success(self):
        """
        Test successful AI message processing with BackgroundTasks.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        # Return an iterator for streaming response
        mock_brain.send_message_ai.return_value = iter(["AI ", "response"])
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        message_data = MessageRequest(
            user_message="Tell me a workout plan."
        ).model_dump()

        # Act
        response = self.client.post(
            "/message",
            headers={"Authorization": "Bearer test_token"},
            json=message_data,
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        # StreamingResponse returns text/plain, not JSON
        self.assertEqual(response.text, "AI response")

        # Verify send_message_ai was called with correct parameters including background_tasks
        mock_brain.send_message_ai.assert_called_once()
        call_args = mock_brain.send_message_ai.call_args
        self.assertEqual(call_args[1]["user_email"], "test@test.com")
        self.assertEqual(call_args[1]["user_input"], "Tell me a workout plan.")
        # Verify background_tasks parameter exists (FastAPI injects it)
        self.assertIn("background_tasks", call_args[1])

        app.dependency_overrides = {}

    def test_message_ai_brain_error(self):
        """
        Test AI message processing when AITrainerBrain raises ValueError.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.send_message_ai.side_effect = ValueError(
            "User profile not found for email: test@test.com"
        )
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        message_data = MessageRequest(
            user_message="Tell me a workout plan."
        ).model_dump()

        # Act
        response = self.client.post(
            "/message",
            headers={"Authorization": "Bearer test_token"},
            json=message_data,
        )

        # Assert
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {"detail": "User profile not found for email: test@test.com"},
        )
        app.dependency_overrides = {}

    def test_message_ai_unauthenticated(self):
        """
        Test AI message processing without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user
        message_data = MessageRequest(
            user_message="Tell me a workout plan."
        ).model_dump()

        # Act
        response = self.client.post("/message", json=message_data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}

    def test_update_trainer_profile_success(self):
        """
        Test successful update of trainer profile.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.save_trainer_profile.return_value = (
            None  # Assuming save_trainer_profile returns None
        )
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
        profile_data = TrainerProfileInput(trainer_type="atlas").model_dump()

        # Act
        response = self.client.put(
            "/trainer/update_trainer_profile",
            headers={"Authorization": "Bearer test_token"},
            json=profile_data,
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["trainer_type"], "atlas")
        self.assertEqual(response_data["user_email"], "test@test.com")
        mock_brain.save_trainer_profile.assert_called_once()
        app.dependency_overrides = {}

    def test_update_trainer_profile_unauthenticated(self):
        """
        Test update of trainer profile without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user

        profile_data = TrainerProfileInput(trainer_type="atlas").model_dump()

        # Act
        response = self.client.put("/trainer/update_trainer_profile", json=profile_data)

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}

    def test_get_trainer_profile_success(self):
        """
        Test successful retrieval of trainer profile.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_trainer_profile.return_value = TrainerProfile(
            user_email="test@test.com", trainer_type="atlas"
        )
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get(
            "/trainer/trainer_profile", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trainer_type"], "atlas")
        app.dependency_overrides = {}

    def test_get_trainer_profile_returns_default(self):
        """
        Test that retrieval of non-existent trainer profile returns default.
        """
        # Arrange
        app.dependency_overrides[verify_token] = lambda: "test@test.com"
        mock_brain = MagicMock()
        mock_brain.get_trainer_profile.return_value = None
        app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

        # Act
        response = self.client.get(
            "/trainer/trainer_profile", headers={"Authorization": "Bearer test_token"}
        )

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["trainer_type"], "atlas")
        app.dependency_overrides = {}

    def test_get_trainer_profile_unauthenticated(self):
        """
        Test retrieval of trainer profile without authentication.
        """
        # Arrange
        app.dependency_overrides[verify_token] = mock_unauthenticated_user

        # Act
        response = self.client.get("/trainer/trainer_profile")

        # Assert
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"detail": "Not authenticated"})
        app.dependency_overrides = {}


if __name__ == "__main__":
    unittest.main()
