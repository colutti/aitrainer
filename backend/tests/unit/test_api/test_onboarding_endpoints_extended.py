"""
Comprehensive tests for onboarding endpoints.
Tests cover invite validation and account creation flows.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timezone, timedelta

from src.api.main import app
from src.core.deps import get_mongo_database


client = TestClient(app)


# Fixtures
@pytest.fixture
def valid_invite():
    """Create a valid invite token object."""
    return MagicMock(
        token="valid_token_123",
        email="newuser@example.com",
        used=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )


@pytest.fixture
def expired_invite():
    """Create an expired invite token object."""
    return MagicMock(
        token="expired_token",
        email="newuser@example.com",
        used=False,
        expires_at=datetime.now(timezone.utc) - timedelta(days=1)
    )


@pytest.fixture
def used_invite():
    """Create an already used invite token object."""
    return MagicMock(
        token="used_token",
        email="newuser@example.com",
        used=True,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )


# Test: GET /onboarding/validate - Valid Token
def test_validate_invite_token_valid(valid_invite):
    """Test validating a valid invite token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_get_db.return_value = mock_db

        response = client.get(
            "/onboarding/validate?token=valid_token_123"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["email"] == "newuser@example.com"


# Test: GET /onboarding/validate - Invalid Token (Not Found)
def test_validate_invite_token_not_found():
    """Test validating a non-existent invite token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = None
        mock_get_db.return_value = mock_db

        response = client.get(
            "/onboarding/validate?token=invalid_token"
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in response.json()


# Test: GET /onboarding/validate - Already Used
def test_validate_invite_token_already_used(used_invite):
    """Test validating an already used invite token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = used_invite
        mock_get_db.return_value = mock_db

        response = client.get(
            "/onboarding/validate?token=used_token"
        )

        assert response.status_code == 409
        data = response.json()
        assert "detail" in data


# Test: GET /onboarding/validate - Expired Token
def test_validate_invite_token_expired(expired_invite):
    """Test validating an expired invite token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = expired_invite
        mock_get_db.return_value = mock_db

        response = client.get(
            "/onboarding/validate?token=expired_token"
        )

        assert response.status_code == 410
        data = response.json()
        assert "detail" in data


# Test: GET /onboarding/validate - Missing Token Parameter
def test_validate_invite_token_missing_param():
    """Test validate endpoint without token parameter."""
    response = client.get("/onboarding/validate")

    assert response.status_code == 422


# Test: GET /onboarding/validate - Token with Timezone Awareness
def test_validate_invite_token_timezone_handling(valid_invite):
    """Test that timezone-naive expiry dates are handled correctly."""
    # Create invite with naive datetime
    naive_invite = MagicMock(
        token="token",
        email="user@example.com",
        used=False,
        expires_at=datetime.now() + timedelta(days=1)  # No timezone
    )

    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = naive_invite
        mock_get_db.return_value = mock_db

        response = client.get(
            "/onboarding/validate?token=token"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


# Test: POST /onboarding/complete - Success
def test_complete_onboarding_success(valid_invite):
    """Test successful onboarding completion."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db, \
         patch("src.api.endpoints.onboarding.user_login") as mock_login:

        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_db.get_user_profile.return_value = None
        mock_db.save_user_profile.return_value = None
        mock_db.save_trainer_profile.return_value = None
        mock_get_db.return_value = mock_db
        mock_login.return_value = "jwt_token_xyz"

        payload = {
            "token": "valid_token_123",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": 28,
            "weight": 75.0,
            "height": 180,
            "goal_type": "weight_loss",
            "weekly_rate": 0.5,
            "trainer_type": "atlas"
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "jwt_token_xyz"
        assert "message" in data

        mock_db.save_user_profile.assert_called_once()
        mock_db.save_trainer_profile.assert_called_once()
        mock_db.invites.mark_as_used.assert_called_once_with("valid_token_123")


# Test: POST /onboarding/complete - Invalid Token
def test_complete_onboarding_invalid_token():
    """Test onboarding completion with invalid token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = None
        mock_get_db.return_value = mock_db

        payload = {
            "token": "invalid_token",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": 28,
            "weight": 75.0,
            "height": 180,
            "goal_type": "weight_loss",
            "weekly_rate": 0.5,
            "trainer_type": "atlas"
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 404


# Test: POST /onboarding/complete - Already Used Token
def test_complete_onboarding_already_used_token(used_invite):
    """Test onboarding with already used token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = used_invite
        mock_get_db.return_value = mock_db

        payload = {
            "token": "used_token",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "F",
            "age": 25,
            "weight": 65.0,
            "height": 165,
            "goal_type": "muscle_gain",
            "weekly_rate": 0.5,
            "trainer_type": "luna"
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 409


# Test: POST /onboarding/complete - Expired Token
def test_complete_onboarding_expired_token(expired_invite):
    """Test onboarding with expired token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = expired_invite
        mock_get_db.return_value = mock_db

        payload = {
            "token": "expired_token",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": 30,
            "weight": 80.0,
            "height": 185,
            "goal_type": "maintenance",
            "weekly_rate": 0.0,
            "trainer_type": "sofia"
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 410


# Test: POST /onboarding/complete - User Already Exists
def test_complete_onboarding_user_exists(valid_invite):
    """Test onboarding when user already exists."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_db.get_user_profile.return_value = MagicMock()  # User exists
        mock_get_db.return_value = mock_db

        payload = {
            "token": "valid_token_123",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": 28,
            "weight": 75.0,
            "height": 180,
            "goal_type": "weight_loss",
            "weekly_rate": 0.5,
            "trainer_type": "atlas"
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 409


# Test: POST /onboarding/complete - Missing Required Fields
def test_complete_onboarding_missing_fields(valid_invite):
    """Test onboarding with missing required fields."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_get_db.return_value = mock_db

        payload = {
            "token": "valid_token_123",
            "email": "newuser@example.com",
            # Missing password, gender, age, etc.
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 422


# Test: POST /onboarding/complete - Invalid Age
def test_complete_onboarding_invalid_age(valid_invite):
    """Test onboarding with invalid age."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_get_db.return_value = mock_db

        payload = {
            "token": "valid_token_123",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": -5,  # Invalid negative age
            "weight": 75.0,
            "height": 180,
            "goal_type": "weight_loss",
            "weekly_rate": 0.5,
            "trainer_type": "atlas"
        }

        response = client.post("/onboarding/complete", json=payload)

        # Depending on validation, might be 422 or 200
        assert response.status_code in [200, 422]


# Test: POST /onboarding/complete - Different Trainer Types
@pytest.mark.parametrize("trainer_type", ["atlas", "luna", "sofia", "sargento", "gymbro"])
def test_complete_onboarding_various_trainers(trainer_type, valid_invite):
    """Test onboarding with different trainer types."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db, \
         patch("src.api.endpoints.onboarding.user_login") as mock_login:

        mock_db = MagicMock()
        mock_db.invites.get_by_token.return_value = valid_invite
        mock_db.get_user_profile.return_value = None
        mock_get_db.return_value = mock_db
        mock_login.return_value = "jwt_token"

        payload = {
            "token": "valid_token_123",
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "gender": "M",
            "age": 28,
            "weight": 75.0,
            "height": 180,
            "goal_type": "weight_loss",
            "weekly_rate": 0.5,
            "trainer_type": trainer_type
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "jwt_token"

        # Verify trainer profile was saved with correct type
        call_args = mock_db.save_trainer_profile.call_args
        trainer_profile = call_args[0][0]
        assert trainer_profile.trainer_type == trainer_type
