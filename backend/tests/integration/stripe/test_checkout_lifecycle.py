"""Integration tests for checkout/subscription lifecycle webhook handling."""

from __future__ import annotations

import json
import time
from types import SimpleNamespace
from unittest.mock import patch

import stripe


def _signature_for(payload: bytes, secret: str) -> str:
    timestamp = int(time.time())
    signature = stripe.WebhookSignature._compute_signature(  # pylint: disable=protected-access
        f"{timestamp}.{payload.decode()}",
        secret=secret,
    )
    return f"t={timestamp},v1={signature}"


def _post_signed_event(client, event: dict, secret: str):
    payload = json.dumps(event).encode()
    signature = _signature_for(payload, secret)
    return client.post(
        "/stripe/webhook",
        content=payload,
        headers={"stripe-signature": signature},
    )


def _settings(secret: str) -> SimpleNamespace:
    return SimpleNamespace(
        STRIPE_WEBHOOK_SECRET=secret,
        STRIPE_PRICE_ID_PRO="price_pro",
        STRIPE_PRICE_ID_PRO_USD="",
        STRIPE_PRICE_ID_PRO_BRL="",
        STRIPE_PRICE_ID_PRO_EUR="",
    )


def test_checkout_completed_maps_customer_to_user(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("checkout@example.com", plan="Free")
    assert profile.stripe_customer_id is None

    event = {
        "id": "evt_checkout_completed",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_123",
                "customer": "cus_checkout",
                "metadata": {"user_email": "checkout@example.com"},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_checkout")):
        response = _post_signed_event(client, event, "whsec_checkout")

    assert response.status_code == 200
    assert brain.get_user_profile("checkout@example.com").stripe_customer_id == "cus_checkout"


def test_subscription_created_promotes_user_to_pro(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("pro@example.com", plan="Free")
    profile.stripe_customer_id = "cus_pro"
    profile.messages_sent_this_month = 42
    profile.photos_sent_this_month = 3
    brain.emails_by_customer_id["cus_pro"] = "pro@example.com"

    event = {
        "id": "evt_sub_created",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_pro",
                "status": "active",
                "current_period_start": int(time.time()),
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_sub_created")):
        response = _post_signed_event(client, event, "whsec_sub_created")

    assert response.status_code == 200
    updated = brain.get_user_profile("pro@example.com")
    assert updated.subscription_plan == "Pro"
    assert updated.stripe_subscription_status == "active"
    assert updated.messages_sent_this_month == 0
    assert updated.photos_sent_this_month == 0


def test_live_stripe_harness_can_create_customer_when_enabled(
    stripe_live_client, stripe_test_run_id, cleanup_registry
):
    email = f"{stripe_test_run_id}@example.com"
    customer = stripe_live_client.create_customer(email=email, test_run_id=stripe_test_run_id)
    cleanup_registry.add(lambda: stripe_live_client.client.customers.delete(customer.id))

    assert customer.email == email
    assert customer.metadata.get("test_run_id") == stripe_test_run_id
