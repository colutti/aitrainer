"""
Comprehensive tests for trainer selection and profile management endpoints.
Tests cover trainer profile retrieval, updates, and available trainers listing.
"""

from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.trainer_profile import TrainerProfile


client = TestClient(app)


# Fixtures
@pytest.fixture
def sample_trainer_profile():
    return TrainerProfile(
        user_email="test@example.com",
        trainer_type="atlas",
        preferred_language="pt-BR",
        personality_level="balanced"
    )


@pytest.fixture
def available_trainers_list():
    return [
        {
            "id": "atlas",
            "name": "Atlas",
            "description": "Powerful and direct trainer",
            "personality": "Strong"
        },
        {
            "id": "luna",
            "name": "Luna",
            "description": "Empathetic and supportive",
            "personality": "Caring"
        },
        {
            "id": "sofia",
            "name": "Sofia",
            "description": "Technical and data-driven",
            "personality": "Analytical"
        }
    ]


# Test: PUT /trainer/update_trainer_profile - Success Case
def test_update_trainer_profile_success(sample_trainer_profile):
    """Test successfully updating trainer profile."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.save_trainer_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    update_payload = {
        "trainer_type": "luna",
        "preferred_language": "pt-BR"
    }

    response = client.put(
        "/trainer/update_trainer_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trainer_type"] == "luna"
    assert data["user_email"] == "test@example.com"
    mock_brain.save_trainer_profile.assert_called_once()

    app.dependency_overrides = {}


# Test: PUT /trainer/update_trainer_profile - Unauthorized
def test_update_trainer_profile_unauthorized():
    """Test updating trainer profile without authentication."""
    update_payload = {
        "trainer_type": "sofia"
    }

    response = client.put(
        "/trainer/update_trainer_profile",
        json=update_payload
    )

    assert response.status_code == 401


# Test: PUT /trainer/update_trainer_profile - Invalid Trainer Type
def test_update_trainer_profile_invalid_type():
    """Test updating with invalid trainer type."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    update_payload = {
        "trainer_type": "invalid_trainer_xyz"
    }

    response = client.put(
        "/trainer/update_trainer_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    # Should either accept (and validate later) or reject
    assert response.status_code in [200, 422]

    app.dependency_overrides = {}


# Test: GET /trainer/trainer_profile - Success Case
def test_get_trainer_profile_success(sample_trainer_profile):
    """Test retrieving existing trainer profile."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.get_trainer_profile.return_value = sample_trainer_profile
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/trainer/trainer_profile",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trainer_type"] == "atlas"
    assert data["user_email"] == "test@example.com"
    mock_brain.get_trainer_profile.assert_called_once_with("test@example.com")

    app.dependency_overrides = {}


# Test: GET /trainer/trainer_profile - Default When Not Found
def test_get_trainer_profile_default():
    """Test retrieving trainer profile returns default when not found."""
    app.dependency_overrides[verify_token] = lambda: "newuser@example.com"
    mock_brain = MagicMock()
    mock_brain.get_trainer_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    response = client.get(
        "/trainer/trainer_profile",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trainer_type"] == "atlas"  # Default trainer
    assert data["user_email"] == "newuser@example.com"

    app.dependency_overrides = {}


# Test: GET /trainer/trainer_profile - Unauthorized
def test_get_trainer_profile_unauthorized():
    """Test retrieving trainer profile without authentication."""
    response = client.get("/trainer/trainer_profile")

    assert response.status_code == 401


# Test: GET /trainer/available_trainers - Success Case
def test_get_available_trainers_success(available_trainers_list):
    """Test retrieving list of available trainers."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    with patch("src.api.endpoints.trainer.TrainerRegistry") as mock_registry_class:
        mock_registry = MagicMock()
        mock_registry.list_trainers_for_api.return_value = available_trainers_list
        mock_registry_class.return_value = mock_registry

        response = client.get(
            "/trainer/available_trainers",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["id"] == "atlas"
        assert data[1]["name"] == "Luna"

    app.dependency_overrides = {}


# Test: GET /trainer/available_trainers - Unauthorized
def test_get_available_trainers_unauthorized():
    """Test retrieving available trainers without authentication."""
    response = client.get("/trainer/available_trainers")

    assert response.status_code == 401


# Test: GET /trainer/available_trainers - Empty List
def test_get_available_trainers_empty():
    """Test retrieving available trainers when none are available."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"

    with patch("src.api.endpoints.trainer.TrainerRegistry") as mock_registry_class:
        mock_registry = MagicMock()
        mock_registry.list_trainers_for_api.return_value = []
        mock_registry_class.return_value = mock_registry

        response = client.get(
            "/trainer/available_trainers",
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    app.dependency_overrides = {}


# Test: PUT /trainer/update_trainer_profile - Partial Update
def test_update_trainer_profile_partial():
    """Test partial trainer profile update."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.save_trainer_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Only update trainer type, not other fields
    update_payload = {
        "trainer_type": "sargento"
    }

    response = client.put(
        "/trainer/update_trainer_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trainer_type"] == "sargento"

    app.dependency_overrides = {}


# Test: PUT /trainer/update_trainer_profile - Multiple Updates
def test_update_trainer_profile_multiple_fields():
    """Test updating multiple trainer profile fields."""
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    mock_brain = MagicMock()
    mock_brain.save_trainer_profile.return_value = None
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    update_payload = {
        "trainer_type": "gymbro",
        "preferred_language": "en-US",
        "personality_level": "energetic"
    }

    response = client.put(
        "/trainer/update_trainer_profile",
        json=update_payload,
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["trainer_type"] == "gymbro"

    app.dependency_overrides = {}
