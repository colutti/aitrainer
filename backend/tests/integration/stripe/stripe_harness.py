"""Helpers for Stripe live integration tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
from typing import Any

import stripe


def wait_until(
    predicate: Callable[[], bool],
    timeout_seconds: float,
    interval_seconds: float,
    description: str,
) -> None:
    """Polls a predicate until true or timeout is reached."""
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval_seconds)
    raise TimeoutError(description)


@dataclass(slots=True)
class CleanupRegistry:
    """Tracks cleanup callbacks and runs them once in reverse order."""

    callbacks: list[Callable[[], None]] = field(default_factory=list)
    _executed: bool = False

    def add(self, callback: Callable[[], None]) -> None:
        self.callbacks.append(callback)

    def run_all(self) -> None:
        if self._executed:
            return
        self._executed = True
        for callback in reversed(self.callbacks):
            try:
                callback()
            except Exception:
                # Cleanup should not hide real test assertions.
                continue


class StripeLiveHarness:
    """Thin wrapper around Stripe test-mode client operations used by tests."""

    def __init__(self, api_key: str, api_base: str | None = None) -> None:
        self.client = stripe.StripeClient(api_key=api_key)
        self.api_base = api_base

    @staticmethod
    def build_test_metadata(test_run_id: str, user_email: str) -> dict[str, str]:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return {
            "test_run_id": test_run_id,
            "user_email": user_email,
            "correlation_id": f"{test_run_id}-{ts}",
        }

    def create_customer(
        self, email: str, test_run_id: str, metadata: dict[str, str] | None = None
    ) -> Any:
        merged_metadata = {**(metadata or {}), "test_run_id": test_run_id}
        return self.client.customers.create(email=email, metadata=merged_metadata)

    def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        metadata: dict[str, str] | None = None,
    ) -> Any:
        return self.client.subscriptions.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata=metadata or {},
        )

    def cancel_subscription_immediately(self, subscription_id: str) -> Any:
        return self.client.subscriptions.cancel(subscription_id)

    def cancel_subscription_at_period_end(self, subscription_id: str) -> Any:
        return self.client.subscriptions.update(
            subscription_id, cancel_at_period_end=True
        )

    def reactivate_subscription(self, subscription_id: str) -> Any:
        return self.client.subscriptions.update(
            subscription_id, cancel_at_period_end=False
        )

    def swap_subscription_price(
        self, subscription_id: str, item_id: str, new_price_id: str
    ) -> Any:
        return self.client.subscriptions.update(
            subscription_id, items=[{"id": item_id, "price": new_price_id}]
        )

