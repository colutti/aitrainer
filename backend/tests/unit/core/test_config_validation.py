"""Tests for core Settings defaults used by chat memory windowing."""

import pytest
from pydantic import ValidationError


def test_settings_default_short_term_window_is_50():
    """Default short-term prompt window should be 50 messages."""
    from src.core.config import Settings

    settings = Settings()
    assert settings.MAX_SHORT_TERM_MEMORY_MESSAGES == 50


def test_settings_accepts_custom_short_term_window():
    """Custom short-term prompt window should be accepted."""
    from src.core.config import Settings

    settings = Settings(MAX_SHORT_TERM_MEMORY_MESSAGES=30)
    assert settings.MAX_SHORT_TERM_MEMORY_MESSAGES == 30


def test_live_stripe_test_mode_defaults_to_disabled():
    """Live Stripe mode must be opt-in and disabled by default."""
    from src.core.config import Settings

    settings = Settings()
    assert settings.STRIPE_LIVE_TEST_ENABLED is False


def test_live_stripe_requires_test_secret_key_when_enabled():
    """Live Stripe mode should require the test API key."""
    from src.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            STRIPE_LIVE_TEST_ENABLED=True,
            STRIPE_TEST_WEBHOOK_SECRET="whsec_test",
            STRIPE_CLI_WEBHOOK_FORWARD_URL="http://localhost:8000/stripe/webhook",
        )


def test_live_stripe_requires_webhook_secret_when_enabled():
    """Live Stripe mode should require webhook signing secret."""
    from src.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            STRIPE_LIVE_TEST_ENABLED=True,
            STRIPE_TEST_SECRET_KEY="sk_test_123",
            STRIPE_CLI_WEBHOOK_FORWARD_URL="http://localhost:8000/stripe/webhook",
        )


def test_live_stripe_requires_forward_url_when_enabled():
    """Live Stripe mode should require webhook forward URL."""
    from src.core.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            STRIPE_LIVE_TEST_ENABLED=True,
            STRIPE_TEST_SECRET_KEY="sk_test_123",
            STRIPE_TEST_WEBHOOK_SECRET="whsec_test",
        )
