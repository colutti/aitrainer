"""Polling assertions for user profile convergence during Stripe live tests."""

from __future__ import annotations

import time
from typing import Any
from collections.abc import Callable


def wait_for_profile_state(
    get_profile: Callable[[], dict[str, Any]],
    expected: dict[str, Any],
    timeout_seconds: float = 30.0,
    interval_seconds: float = 0.5,
) -> dict[str, Any]:
    """Poll profile until all expected key/value pairs match."""
    deadline = time.monotonic() + timeout_seconds
    last_profile: dict[str, Any] = {}
    while time.monotonic() < deadline:
        last_profile = get_profile()
        if all(last_profile.get(k) == v for k, v in expected.items()):
            return last_profile
        time.sleep(interval_seconds)
    raise TimeoutError(
        f"Profile state did not converge within {timeout_seconds}s. "
        f"Expected={expected}, last={last_profile}"
    )

