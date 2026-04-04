from src.core.subscription import (
    SUBSCRIPTION_PLANS,
    SubscriptionPlan,
    can_use_imports,
    can_use_integrations,
    can_use_image_input,
    can_use_telegram,
)


def test_subscription_plans_have_new_fields():
    for plan, details in SUBSCRIPTION_PLANS.items():
        assert hasattr(details, "daily_limit")
        assert hasattr(details, "validity_days")
        assert hasattr(details, "allowed_trainers")
        assert hasattr(details, "image_input_enabled")
        assert hasattr(details, "integrations_enabled")
        assert hasattr(details, "telegram_enabled")
        assert hasattr(details, "imports_enabled")


def test_subscription_catalog_exposes_only_free_basic_and_pro():
    assert set(SubscriptionPlan) == {
        SubscriptionPlan.FREE,
        SubscriptionPlan.BASIC,
        SubscriptionPlan.PRO,
    }
    assert set(SUBSCRIPTION_PLANS.keys()) == set(SubscriptionPlan)


def test_free_plan_specifics():
    free_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]
    assert free_plan.daily_limit == 20
    assert free_plan.validity_days == 7
    assert free_plan.allowed_trainers == ["gymbro"]
    assert free_plan.image_input_enabled is False
    assert free_plan.integrations_enabled is False
    assert free_plan.telegram_enabled is False
    assert free_plan.imports_enabled is False
    assert free_plan.total_limit is None


def test_basic_and_pro_capabilities():
    basic_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.BASIC]
    pro_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.PRO]

    assert basic_plan.monthly_limit == 100
    assert basic_plan.image_input_enabled is False
    assert basic_plan.integrations_enabled is False
    assert basic_plan.telegram_enabled is False
    assert basic_plan.imports_enabled is False

    assert pro_plan.monthly_limit == 300
    assert pro_plan.image_input_enabled is True
    assert pro_plan.integrations_enabled is True
    assert pro_plan.telegram_enabled is True
    assert pro_plan.imports_enabled is True


def test_plan_capability_helpers_follow_catalog():
    assert can_use_image_input("Pro") is True
    assert can_use_image_input("Free") is False
    assert can_use_image_input("Basic") is False

    assert can_use_integrations("Pro") is True
    assert can_use_integrations("Basic") is False

    assert can_use_telegram("Pro") is True
    assert can_use_telegram("Free") is False

    assert can_use_imports("Pro") is True
    assert can_use_imports("Basic") is False
