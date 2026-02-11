"""
Tests for onboarding API endpoints.
"""

import pytest
from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.models.invite import Invite

client = TestClient(app)

@pytest.fixture
def valid_invite():
    """Fixture for a valid invite."""
    return Invite(
        token=str(uuid.uuid4()),
        email="newuser@test.com",
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=72),
        used=False,
    )

@pytest.fixture
def expired_invite():
    """Fixture for an expired invite."""
    return Invite(
        token=str(uuid.uuid4()),
        email="expired@test.com",
        created_at=datetime.now(timezone.utc) - timedelta(hours=73),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        used=False,
    )

@pytest.fixture
def used_invite():
    """Fixture for a used invite."""
    return Invite(
        token=str(uuid.uuid4()),
        email="used@test.com",
        created_at=datetime.now(timezone.utc) - timedelta(hours=10),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=62),
        used=True,
        used_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )

def test_validate_token_success(valid_invite):
    """Test validating a valid invite token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_db:
        mock_invites = MagicMock()
        mock_invites.get_by_token.return_value = valid_invite
        mock_db.return_value.invites = mock_invites

        response = client.get(f"/onboarding/validate?token={valid_invite.token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["email"] == valid_invite.email

def test_validate_token_not_found():
    """Test validating non-existent token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_db:
        mock_invites = MagicMock()
        mock_invites.get_by_token.return_value = None
        mock_db.return_value.invites = mock_invites

        response = client.get("/onboarding/validate?token=nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["valid"] is False

def test_validate_token_expired(expired_invite):
    """Test validating expired token."""
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_db:
        mock_invites = MagicMock()
        mock_invites.get_by_token.return_value = expired_invite
        mock_db.return_value.invites = mock_invites

        response = client.get(f"/onboarding/validate?token={expired_invite.token}")

        assert response.status_code == 410

def test_complete_onboarding_success(valid_invite):
    """Test completing onboarding successfully."""
    with (
        patch("src.api.endpoints.onboarding.get_mongo_database") as mock_db,
        patch("src.api.endpoints.onboarding.user_login") as mock_login,
    ):
        mock_invites = MagicMock()
        mock_invites.get_by_token.return_value = valid_invite
        mock_invites.mark_as_used.return_value = True

        mock_db_instance = MagicMock()
        mock_db_instance.invites = mock_invites
        mock_db_instance.get_user_profile.return_value = None
        mock_db.return_value = mock_db_instance

        mock_login.return_value = "fake-jwt-token"

        request_data = {
            "token": valid_invite.token,
            "password": "SecurePass1",
            "gender": "Masculino",
            "age": 30,
            "weight": 75.0,
            "height": 175,
            "goal_type": "maintain",
            "weekly_rate": 0.5,
            "trainer_type": "atlas",
        }

        response = client.post("/onboarding/complete", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "fake-jwt-token"
        mock_db_instance.save_user_profile.assert_called_once()
        mock_db_instance.save_trainer_profile.assert_called_once()
        mock_invites.mark_as_used.assert_called_once_with(valid_invite.token)

@pytest.mark.parametrize("trainer_type", ["atlas", "luna", "sofia", "sargento"])
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
            "token": valid_invite.token,
            "password": "SecurePassword123!",
            "gender": "Masculino",
            "age": 28,
            "weight": 75.0,
            "height": 180,
            "goal_type": "lose",
            "weekly_rate": 0.5,
            "trainer_type": trainer_type
        }

        response = client.post("/onboarding/complete", json=payload)

        assert response.status_code == 200
        assert mock_db.save_trainer_profile.called
        profile = mock_db.save_trainer_profile.call_args[0][0]
        assert profile.trainer_type == trainer_type
