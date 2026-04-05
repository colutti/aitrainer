"""Core tests for live Stripe harness utilities."""

from datetime import datetime, timezone

import pytest

from .profile_assertions import wait_for_profile_state
from .stripe_harness import CleanupRegistry, StripeLiveHarness, wait_until


def test_generates_unique_metadata_correlation() -> None:
    first = StripeLiveHarness.build_test_metadata("run-a", "test@example.com")
    second = StripeLiveHarness.build_test_metadata("run-b", "test@example.com")

    assert first["test_run_id"] == "run-a"
    assert second["test_run_id"] == "run-b"
    assert first["user_email"] == "test@example.com"
    assert first != second


def test_cleanup_registry_is_idempotent() -> None:
    calls: list[str] = []

    def cleanup_a() -> None:
        calls.append("a")

    def cleanup_b() -> None:
        calls.append("b")
        raise RuntimeError("ignore on cleanup")

    registry = CleanupRegistry()
    registry.add(cleanup_a)
    registry.add(cleanup_b)
    registry.add(cleanup_a)

    registry.run_all()
    registry.run_all()

    assert calls == ["a", "b", "a"]


def test_wait_until_times_out_with_clear_message() -> None:
    started_at = datetime.now(timezone.utc)
    with pytest.raises(TimeoutError, match="did not converge"):
        wait_until(
            predicate=lambda: False,
            timeout_seconds=0.2,
            interval_seconds=0.05,
            description="did not converge",
        )
    elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()
    assert elapsed >= 0.2


def test_wait_for_profile_state_converges() -> None:
    snapshots = iter(
        [
            {"subscription_plan": "Free", "stripe_subscription_status": "incomplete"},
            {"subscription_plan": "Pro", "stripe_subscription_status": "active"},
        ]
    )

    profile = wait_for_profile_state(
        get_profile=lambda: next(snapshots),
        expected={
            "subscription_plan": "Pro",
            "stripe_subscription_status": "active",
        },
        timeout_seconds=1,
        interval_seconds=0.01,
    )

    assert profile["subscription_plan"] == "Pro"

