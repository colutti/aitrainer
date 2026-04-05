"""Integration tests for webhook idempotency and out-of-order delivery."""

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


def test_out_of_order_subscription_update_does_not_rewind_cycle(webhook_test_client):
    client, brain = webhook_test_client
    profile = brain.seed_user("order@example.com", plan="Pro")
    profile.stripe_customer_id = "cus_order"
    profile.messages_sent_this_month = 11
    profile.photos_sent_this_month = 2
    newest_cycle = datetime.now(timezone.utc)
    oldest_cycle = newest_cycle - timedelta(days=31)
    profile.current_billing_cycle_start = newest_cycle.isoformat()
    brain.emails_by_customer_id["cus_order"] = "order@example.com"

    stale_event = {
        "id": "evt_stale",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_order",
                "customer": "cus_order",
                "status": "active",
                "current_period_start": int(oldest_cycle.timestamp()),
                "items": {"data": [{"price": {"id": "price_pro"}}]},
            }
        },
    }

    with patch("src.api.endpoints.stripe.settings", _settings("whsec_order")):
        response = _post_signed_event(client, stale_event, "whsec_order")

    assert response.status_code == 200
    updated = brain.get_user_profile("order@example.com")
    assert updated.current_billing_cycle_start == newest_cycle.isoformat()
    assert updated.messages_sent_this_month == 11
    assert updated.photos_sent_this_month == 2
