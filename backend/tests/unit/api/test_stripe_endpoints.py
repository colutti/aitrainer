"""
Tests for Stripe API endpoints.
"""
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import pytest

from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.api.models.user_profile import UserProfile

client = TestClient(app)

@pytest.fixture
def mock_user_email():
    return "test@example.com"

@pytest.fixture
def sample_user_profile():
    return UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        weight=75.0,
        height=180,
        goal_type="lose",
        subscription_plan="Free",
        onboarding_completed=True,
        stripe_customer_id="cus_test123"
    )

def test_create_checkout_session_success(mock_user_email, sample_user_profile):
    """
    Test successful creation of a Stripe checkout session.
    Verifies that the backend correctly handles the JSON body.
    """
    app.dependency_overrides[verify_token] = lambda: mock_user_email
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = sample_user_profile
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    # Mock the stripe service function
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.api.endpoints.stripe.create_checkout_session", 
                   lambda profile, price_id, success_url, cancel_url: "https://stripe.com/checkout/session")

        payload = {
            "price_id": "price_123",
            "success_url": "http://localhost:3000/success",
            "cancel_url": "http://localhost:3000/cancel"
        }

        response = client.post(
            "/stripe/create-checkout-session",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://stripe.com/checkout/session"

    app.dependency_overrides.clear()

def test_create_checkout_session_invalid_body(mock_user_email):
    """
    Test failure when parameters are sent as query params instead of body.
    This would have failed before the fix with 422 if the frontend kept sending body.
    Now it ensures we explicitly require the body.
    """
    app.dependency_overrides[verify_token] = lambda: mock_user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: MagicMock()

    # Try sending as query params (which was the old expected way but frontend sent body)
    # Now that we expect a body, sending nothing in the body should fail with 422.
    response = client.post(
        "/stripe/create-checkout-session?price_id=price_123&success_url=s&cancel_url=c",
        headers={"Authorization": "Bearer test_token"}
    )

    assert response.status_code == 422
    
    app.dependency_overrides.clear()

def test_create_portal_session_success(mock_user_email, sample_user_profile):
    """Test successful creation of a customer portal session."""
    app.dependency_overrides[verify_token] = lambda: mock_user_email
    mock_brain = MagicMock()
    mock_brain.get_user_profile.return_value = sample_user_profile
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.api.endpoints.stripe.create_customer_portal_session", 
                   lambda customer_id, return_url: "https://stripe.com/portal/session")

        payload = {
            "return_url": "http://localhost:3000/settings"
        }

        response = client.post(
            "/stripe/create-portal-session",
            json=payload,
            headers={"Authorization": "Bearer test_token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["url"] == "https://stripe.com/portal/session"

    app.dependency_overrides.clear()
