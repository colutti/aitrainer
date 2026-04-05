"""Integration tests for billing-cycle reset behavior."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone, timedelta
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


def test_cycle_change_resets_message_and_photo_counters(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("cycle@example.com", plan="Pro")
    profile.stripe_customer_id = "cus_cycle"
    profile.messages_sent_this_month = 12
    profile.photos_sent_this_month = 5
    old_start = datetime.now(timezone.utc) - timedelta(days=35)
    profile.current_billing_cycle_start = old_start.isoformat()
    brain.emails_by_customer_id["cus_cycle"] = "cycle@example.com"

    event = {
        "id": "evt_cycle_new",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_cycle",
                "customer": "cus_cycle",
                "status": "active",
                "current_period_start": int(datetime.now(timezone.utc).timestamp()),
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_cycle")):
        response = _post_signed_event(client, event, "whsec_cycle")

    assert response.status_code == 200
    updated = brain.get_user_profile("cycle@example.com")
    assert updated.messages_sent_this_month == 0
    assert updated.photos_sent_this_month == 0


def test_subscription_deleted_resets_to_free(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("deleted@example.com", plan="Pro")
    profile.stripe_customer_id = "cus_deleted"
    profile.trainer_id = "breno"
    brain.emails_by_customer_id["cus_deleted"] = "deleted@example.com"

    event = {
        "id": "evt_deleted",
        "type": "customer.subscription.deleted",
        "data": {"object": {"id": "sub_deleted", "customer": "cus_deleted"}},
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_deleted")):
        response = _post_signed_event(client, event, "whsec_deleted")

    assert response.status_code == 200
    updated = brain.get_user_profile("deleted@example.com")
    assert updated.subscription_plan == "Free"
    assert updated.stripe_subscription_status == "canceled"
    assert updated.trainer_id == "gymbro"
