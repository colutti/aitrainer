"""Integration tests for subscription state transitions."""

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


def test_past_due_downgrades_to_free_and_resets_counters(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("pastdue@example.com", plan="Pro")
    profile.stripe_customer_id = "cus_past_due"
    profile.messages_sent_this_month = 99
    brain.emails_by_customer_id["cus_past_due"] = "pastdue@example.com"

    event = {
        "id": "evt_past_due",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_past_due",
                "customer": "cus_past_due",
                "status": "past_due",
                "current_period_start": int(time.time()),
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_past_due")):
        response = _post_signed_event(client, event, "whsec_past_due")

    assert response.status_code == 200
    updated = brain.get_user_profile("pastdue@example.com")
    assert updated.subscription_plan == "Free"
    assert updated.messages_sent_this_month == 0
    assert updated.trainer_id == "gymbro"


def test_unpaid_downgrades_to_free(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("unpaid@example.com", plan="Pro")
    profile.stripe_customer_id = "cus_unpaid"
    brain.emails_by_customer_id["cus_unpaid"] = "unpaid@example.com"

    event = {
        "id": "evt_unpaid",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_unpaid",
                "customer": "cus_unpaid",
                "status": "unpaid",
                "current_period_start": int(time.time()),
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_unpaid")):
        response = _post_signed_event(client, event, "whsec_unpaid")

    assert response.status_code == 200
    updated = brain.get_user_profile("unpaid@example.com")
    assert updated.subscription_plan == "Free"
    assert updated.stripe_subscription_status == "unpaid"


def test_duplicate_webhook_delivery_is_idempotent(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("dup@example.com", plan="Free")
    profile.stripe_customer_id = "cus_dup"
    brain.emails_by_customer_id["cus_dup"] = "dup@example.com"

    cycle_start = int(time.time())
    event = {
        "id": "evt_duplicate",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_dup",
                "customer": "cus_dup",
                "status": "active",
                "current_period_start": cycle_start,
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_dup")):
        first_response = _post_signed_event(client, event, "whsec_dup")
        second_response = _post_signed_event(client, event, "whsec_dup")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    updated = brain.get_user_profile("dup@example.com")
    assert updated.subscription_plan == "Pro"
    assert updated.messages_sent_this_month == 0
