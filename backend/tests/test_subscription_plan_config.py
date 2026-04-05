from src.core.subscription import (
    SUBSCRIPTION_PLANS,
    SubscriptionPlan,
    can_use_imports,
    can_use_integrations,
    can_use_chat,
    can_use_image_input,
    can_use_telegram,
    default_trial_ends_at,
)
from datetime import datetime, timedelta, timezone


def test_subscription_plans_have_new_fields():
    for plan, details in SUBSCRIPTION_PLANS.items():
        assert hasattr(details, "monthly_message_limit")
        assert hasattr(details, "monthly_photo_limit")
        assert hasattr(details, "allowed_trainers")
        assert hasattr(details, "chat_enabled")
        assert hasattr(details, "image_input_enabled")
        assert hasattr(details, "integrations_enabled")
        assert hasattr(details, "telegram_enabled")
        assert hasattr(details, "imports_enabled")


def test_subscription_catalog_exposes_only_free_and_pro():
    assert set(SubscriptionPlan) == {
        SubscriptionPlan.FREE,
        SubscriptionPlan.PRO,
    }
    assert set(SUBSCRIPTION_PLANS.keys()) == set(SubscriptionPlan)


def test_free_plan_specifics():
    free_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]
    assert free_plan.monthly_message_limit is None
    assert free_plan.monthly_photo_limit is None
    assert free_plan.chat_enabled is False
    assert free_plan.allowed_trainers == ["gymbro"]
    assert free_plan.image_input_enabled is False
    assert free_plan.integrations_enabled is False
    assert free_plan.telegram_enabled is False
    assert free_plan.imports_enabled is False


def test_pro_capabilities():
    pro_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.PRO]

    assert pro_plan.monthly_message_limit == 500
    assert pro_plan.monthly_photo_limit == 15
    assert pro_plan.chat_enabled is True
    assert pro_plan.image_input_enabled is True
    assert pro_plan.integrations_enabled is True
    assert pro_plan.telegram_enabled is True
    assert pro_plan.imports_enabled is True


def test_plan_capability_helpers_follow_effective_trial():
    active_trial = datetime.now(timezone.utc) + timedelta(days=2)
    expired_trial = datetime.now(timezone.utc) - timedelta(days=1)

    assert can_use_chat("Pro") is True
    assert can_use_chat("Free", active_trial) is True
    assert can_use_chat("Free", expired_trial) is False

    assert can_use_image_input("Pro") is True
    assert can_use_image_input("Free", active_trial) is True
    assert can_use_image_input("Free", expired_trial) is False

    assert can_use_integrations("Pro") is True
    assert can_use_integrations("Free", active_trial) is True
    assert can_use_integrations("Free", expired_trial) is False

    assert can_use_telegram("Pro") is True
    assert can_use_telegram("Free", active_trial) is True
    assert can_use_telegram("Free", expired_trial) is False

    assert can_use_imports("Pro") is True
    assert can_use_imports("Free", active_trial) is True
    assert can_use_imports("Free", expired_trial) is False


def test_default_trial_end_is_future():
    assert default_trial_ends_at() > datetime.now(timezone.utc)
