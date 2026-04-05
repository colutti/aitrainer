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
                        {"price": {"id": "price_pro"}}
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
        mock_settings.STRIPE_PRICE_ID_PRO = "price_pro"
        mock_settings.STRIPE_PRICE_ID_PRO_USD = ""
        mock_settings.STRIPE_PRICE_ID_PRO_BRL = ""
        mock_settings.STRIPE_PRICE_ID_PRO_EUR = ""
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
    assert updates["subscription_plan"] == "Pro"
    assert updates["stripe_subscription_id"] == "sub_123"
    assert updates["custom_message_limit"] is None
    assert updates["photos_sent_this_month"] == 0

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

def test_webhook_subscription_deleted(mock_brain, mock_stripe_construct_event):
    # Setup mock event
    mock_stripe_construct_event.return_value = {
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123"
            }
        }
    }
    
    # Mock settings and brain data
    mock_user = MagicMock(email="test@example.com")
    mock_brain.database.users.find_by_stripe_customer_id.return_value = mock_user
    
    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"}
        )
    
    assert response.status_code == 200
    mock_brain.update_user_profile_fields.assert_called_with(
        "test@example.com",
        {
            "stripe_subscription_status": "canceled",
            "subscription_plan": "Free",
            "stripe_subscription_id": None,
            "photos_sent_this_month": 0,
            "messages_sent_this_month": 0,
        }
    )

def test_webhook_subscription_updated_fallback(mock_brain, mock_stripe_construct_event):
    """Test fallback to metadata email if customer_id not yet mapped (race condition)."""
    now_ts = datetime.now().timestamp()
    mock_stripe_construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_fallback",
                "status": "active",
                "current_period_start": now_ts,
                "items": {
                    "data": [
                        {"price": {"id": "price_pro_brl"}}
                    ]
                },
                "metadata": {
                    "user_email": "fallback@example.com"
                }
            }
        }
    }
    
    # 1. Lookup by customer_id fails
    mock_brain.database.users.find_by_stripe_customer_id.return_value = None
    
    # 2. Lookup by email succeeds
    mock_user = MagicMock(email="fallback@example.com")
    mock_brain.get_user_profile.return_value = mock_user
    
    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_ID_PRO = "price_pro"
        mock_settings.STRIPE_PRICE_ID_PRO_USD = "price_pro_usd"
        mock_settings.STRIPE_PRICE_ID_PRO_BRL = "price_pro_brl"
        mock_settings.STRIPE_PRICE_ID_PRO_EUR = "price_pro_eur"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"}
        )
    
    assert response.status_code == 200
    
    # Verify both mapping and plan update were called
    # First call: mapping customer_id
    # Second call: updating subscription details
    assert mock_brain.update_user_profile_fields.call_count == 2
    
    # Check mapping call
    mapping_call = mock_brain.update_user_profile_fields.call_args_list[0]
    assert mapping_call[0][0] == "fallback@example.com"
    assert mapping_call[0][1]["stripe_customer_id"] == "cus_fallback"
    
    # Check plan update call
    plan_call = mock_brain.update_user_profile_fields.call_args_list[1]
    assert plan_call[0][0] == "fallback@example.com"
    assert plan_call[0][1]["subscription_plan"] == "Pro"


def test_webhook_subscription_updated_unknown_price_falls_back_to_free(
    mock_brain, mock_stripe_construct_event
):
    now_ts = datetime.now().timestamp()
    mock_stripe_construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_unknown",
                "customer": "cus_123",
                "status": "active",
                "current_period_start": now_ts,
                "items": {"data": [{"price": {"id": "price_unknown"}}]},
            }
        },
    }

    mock_user = MagicMock(email="test@example.com")
    mock_user.subscription_plan = "Pro"
    mock_user.current_billing_cycle_start = None
    mock_brain.database.users.find_by_stripe_customer_id.return_value = mock_user

    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_ID_PRO = "price_pro"
        mock_settings.STRIPE_PRICE_ID_PRO_USD = "price_pro_usd"
        mock_settings.STRIPE_PRICE_ID_PRO_BRL = "price_pro_brl"
        mock_settings.STRIPE_PRICE_ID_PRO_EUR = "price_pro_eur"
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"},
        )

    assert response.status_code == 200
    updates = mock_brain.update_user_profile_fields.call_args[0][1]
    assert updates["subscription_plan"] == "Free"


def test_webhook_subscription_updated_past_due_downgrades_to_free(
    mock_brain, mock_stripe_construct_event
):
    now_ts = datetime.now().timestamp()
    mock_stripe_construct_event.return_value = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_past_due",
                "customer": "cus_999",
                "status": "past_due",
                "current_period_start": now_ts,
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    mock_user = MagicMock(email="test@example.com")
    mock_user.subscription_plan = "Pro"
    mock_user.current_billing_cycle_start = None
    mock_brain.database.users.find_by_stripe_customer_id.return_value = mock_user

    with patch("src.api.endpoints.stripe.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_settings.STRIPE_PRICE_ID_PRO = "price_pro"
        mock_settings.STRIPE_PRICE_ID_PRO_USD = ""
        mock_settings.STRIPE_PRICE_ID_PRO_BRL = ""
        mock_settings.STRIPE_PRICE_ID_PRO_EUR = ""
        response = client.post(
            "/stripe/webhook",
            content=b"{}",
            headers={"stripe-signature": "test_sig"},
        )

    assert response.status_code == 200
    updates = mock_brain.update_user_profile_fields.call_args[0][1]
    assert updates["subscription_plan"] == "Free"
    assert updates["photos_sent_this_month"] == 0
    mock_brain.ensure_trainer_allowed.assert_called_with("test@example.com", "Free")
