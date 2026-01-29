"""
Comprehensive tests for user authentication and profile management endpoints.
Tests cover login, logout, profile retrieval, and profile updates.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token, oauth2_scheme
from src.core.deps import get_ai_trainer_brain
from src.api.models.user_profile import UserProfile, UserProfileInput
from src.core.config import settings


client = TestClient(app)


# Fixtures
@pytest.fixture
def mock_user_email():
    return "test@example.com"


@pytest.fixture
def mock_ai_trainer_brain():
    return MagicMock()


@pytest.fixture
def sample_user_profile():
    return UserProfile(
        email="test@example.com",
        password_hash="hashed_password",
        gender="Masculino",
        age=30,
        weight=75.0,
        height=180,
        goal_type="lose",
        weekly_rate=0.5,
        goal=None,
        target_weight=70.0,
        notes="Test user",
        long_term_summary=None,
        last_compaction_timestamp=None,
        hevy_api_key=None,
        hevy_enabled=False,
        hevy_last_sync=None,
        hevy_webhook_token=None,
        hevy_webhook_secret=None,
    )


# Test: POST /login - Success Case
def test_login_success():
    """Test successful user login with valid credentials."""
    with patch("src.api.endpoints.user.user_login") as mock_login:
        mock_login.return_value = "mock_jwt_token"

        payload = {
            "email": "test@example.com",
            "password": "correct_password"
        }

        response = client.post("/user/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "mock_jwt_token"
        mock_login.assert_called_once_with("test@example.com", "correct_password")


# Test: POST /login - Invalid Credentials
def test_login_invalid_credentials():
    """Test login failure with invalid credentials."""
    with patch("src.api.endpoints.user.user_login") as mock_login:
        mock_login.side_effect = ValueError("Invalid credentials")

        payload = {
            "email": "test@example.com",
            "password": "wrong_password"
        }

        response = client.post("/user/login", json=payload)

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]


# Test: POST /login - Missing Email
def test_login_missing_email():
    """Test login endpoint with missing email field."""
    payload = {
        "password": "some_password"
    }

    response = client.post("/user/login", json=payload)

    assert response.status_code == 422  # Validation error


# Test: GET /profile - Success Case
def test_get_profile_success(sample_user_profile):
    """Test successful profile retrieval for authenticated user."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = sample_user_profile
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/user/profile",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["age"] == 30
    mock_brain.get_user_profile.assert_called_once_with("test@example.com")

    app.dependency_overrides = {}


# Test: GET /profile - Profile Not Found
def test_get_profile_not_found():
    """Test profile retrieval when user profile doesn't exist."""
    app.dependency_overrides[verify_token] = lambda: "nonexistent@example.com"
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/user/profile",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "User profile not found" in data["detail"]

    app.dependency_overrides = {}


# Test: GET /me - Success Case
def test_get_current_user_success(sample_user_profile):
    """Test getting current user info including role."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = sample_user_profile
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/user/me",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "role" in data

    app.dependency_overrides = {}


# Test: GET /me - Unauthorized (No Token)
def test_get_current_user_unauthorized():
    """Test accessing /me without authentication token."""
    response = client.get("/user/me")

    assert response.status_code == 401  # Unauthorized - no token


# Test: POST /update_profile - Success Case
def test_update_profile_success(sample_user_profile):
    """Test successful profile update."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = sample_user_profile
    mock_brain.save_user_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    update_payload = {
        "gender": "Masculino",
        "age": 31,
        "weight": 74.0,
        "height": 180,
        "goal_type": "lose",
        "weekly_rate": 0.5,
        "notes": "Updated note"
    }

    response = client.post(
        "/user/update_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "Profile updated successfully" in data["message"]
    mock_brain.save_user_profile.assert_called_once()

    app.dependency_overrides = {}


# Test: POST /update_profile - New Profile Creation Fallback
def test_update_profile_creates_new():
    """Test profile update creates new profile when none exists."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = None  # No existing profile
    mock_brain.save_user_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    update_payload = {
        "age": 25,
        "weight": 70.0,
        "gender": "Feminino",
        "height": 165,
        "goal_type": "maintain",
        "weekly_rate": 0.5
    }

    response = client.post(
        "/user/update_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    mock_brain.save_user_profile.assert_called_once()

    app.dependency_overrides = {}


# Test: POST /logout - Success Case
def test_logout_success():
    """Test successful user logout."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    with patch("src.api.endpoints.user.oauth2_scheme") as mock_scheme, \
         patch("src.api.endpoints.user.user_logout") as mock_logout:
        mock_scheme.return_value = "Bearer test_token"
        mock_logout.return_value = None

        response = client.post(
            "/user/logout",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Logged out successfully" in data["message"]

    app.dependency_overrides = {}


# Test: POST /logout - Unauthorized
def test_logout_unauthorized():
    """Test logout without authentication token."""
    response = client.post("/user/logout")

    assert response.status_code == 401  # Unauthorized - no token


# Test: GET /profile - Unauthorized (No Token)
def test_get_profile_unauthorized():
    """Test profile retrieval without authentication token."""
    response = client.get("/user/profile")

    assert response.status_code == 401  # Unauthorized - no token


# Test: POST /update_profile - Invalid Request Data
def test_update_profile_invalid_data():
    """Test profile update with invalid data structure."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    # Missing required fields in malformed request
    update_payload = {
        "invalid_field": "value"
    }

    response = client.post(
        "/user/update_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    # Pydantic should handle gracefully or return 200 with partial update
    assert response.status_code in [200, 422]

    app.dependency_overrides = {}
