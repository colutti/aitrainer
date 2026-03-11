import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

@pytest.fixture
def mock_brain():
    brain_instance = MagicMock()
    # Mock the database users property
    brain_instance.database.users = MagicMock()
    
    from src.core.deps import get_ai_trainer_brain
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain_instance
    yield brain_instance
    app.dependency_overrides.pop(get_ai_trainer_brain)

@pytest.fixture
def mock_stripe_construct_event():
    with patch("stripe.Webhook.construct_event") as mock:
        yield mock

def test_webhook_checkout_completed(mock_brain, mock_stripe_construct_event):
    # Setup mock event
    mock_stripe_construct_event.return_value = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_123",
                "metadata": {"user_email": "test@example.com"}
            }
        }
    }
    
    # Mock settings in the endpoint module
    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"}
        )
    
    assert response.status_code == 200
    assert response.json() == {"status": "success"}
    mock_brain.update_user_profile_fields.assert_called_with(
        "test@example.com", {"stripe_customer_id": "cus_123"}
    )

def test_webhook_subscription_updated(mock_brain, mock_stripe_construct_event):
    # Setup mock event
    now_ts = datetime.now().timestamp()
    mock_stripe_construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "current_period_start": now_ts,
                "items": {
                    "data": [
                        {"price": {"id": "price_basic"}}
                    ]
                }
            }
        }
    }
    
    # Mock settings and brain data
    mock_user = MagicMock(email="test@example.com")
    mock_brain.database.users.find_by_stripe_customer_id.return_value = mock_user
    
    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_ID_BASIC = "price_basic"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"}
        )
    
    assert response.status_code == 200
    mock_brain.update_user_profile_fields.assert_called()
    args = mock_brain.update_user_profile_fields.call_args[0]
    assert args[0] == "test@example.com"
    updates = args[1]
    assert updates["subscription_plan"] == "Basic"
    assert updates["stripe_subscription_id"] == "sub_123"
    assert updates["custom_message_limit"] is None

def test_webhook_invalid_signature(mock_stripe_construct_event):
    import stripe
    mock_stripe_construct_event.side_effect = stripe.error.SignatureVerificationError("Invalid", "sig")
    
    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"}
        )
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid signature"
