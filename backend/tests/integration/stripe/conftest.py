"""Pytest fixtures for Stripe live integration tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.core.config import settings
from src.core.deps import get_ai_trainer_brain

from .profile_assertions import wait_for_profile_state
from .stripe_harness import CleanupRegistry, StripeLiveHarness


def _env_true(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class _FakeBrain:
    profiles_by_email: dict[str, SimpleNamespace]
    emails_by_customer_id: dict[str, str]
    database: SimpleNamespace

    def __init__(self) -> None:
        self.profiles_by_email = {}
        self.emails_by_customer_id = {}
        self.database = SimpleNamespace(
            users=SimpleNamespace(find_by_stripe_customer_id=self.find_by_customer_id)
        )

    def seed_user(self, email: str, plan: str = "Free") -> SimpleNamespace:
        now = datetime.now(timezone.utc).isoformat()
        profile = SimpleNamespace(
            email=email,
            subscription_plan=plan,
            stripe_customer_id=None,
            stripe_subscription_id=None,
            stripe_subscription_status=None,
            current_billing_cycle_start=now,
            messages_sent_this_month=0,
            photos_sent_this_month=0,
            trainer_id="gymbro",
        )
        self.profiles_by_email[email] = profile
        return profile

    def get_user_profile(self, email: str) -> SimpleNamespace | None:
        return self.profiles_by_email.get(email)

    def update_user_profile_fields(self, email: str, fields: dict) -> bool:
        profile = self.profiles_by_email[email]
        for key, value in fields.items():
            setattr(profile, key, value)
        if getattr(profile, "stripe_customer_id", None):
            self.emails_by_customer_id[profile.stripe_customer_id] = email
        return True

    def find_by_customer_id(self, customer_id: str):
        email = self.emails_by_customer_id.get(customer_id)
        if not email:
            return None
        return self.profiles_by_email.get(email)

    def ensure_trainer_allowed(self, user_email: str, plan_name: str) -> None:
        profile = self.profiles_by_email[user_email]
        if plan_name == "Free":
            profile.trainer_id = "gymbro"


@pytest.fixture
def stripe_test_run_id() -> str:
    return f"stripe-live-{uuid4().hex[:12]}"


@pytest.fixture
def cleanup_registry():
    registry = CleanupRegistry()
    yield registry
    registry.run_all()


@pytest.fixture
def stripe_live_enabled() -> bool:
    return _env_true(str(settings.STRIPE_LIVE_TEST_ENABLED))


@pytest.fixture
def stripe_live_client(stripe_live_enabled: bool):
    if not stripe_live_enabled:
        pytest.skip("Stripe live tests disabled. Set STRIPE_LIVE_TEST_ENABLED=true")
    if not settings.STRIPE_TEST_SECRET_KEY:
        pytest.skip("Missing STRIPE_TEST_SECRET_KEY for live Stripe tests")
    return StripeLiveHarness(
        api_key=settings.STRIPE_TEST_SECRET_KEY, api_base=settings.STRIPE_API_BASE
    )


@pytest.fixture
def webhook_test_client():
    brain = _FakeBrain()
    app.dependency_overrides[get_ai_trainer_brain] = lambda: brain
    client = TestClient(app)
    try:
        yield client, brain
    finally:
        app.dependency_overrides.pop(get_ai_trainer_brain, None)


@pytest.fixture
def await_profile_state():
    return wait_for_profile_state
