from src.core.subscription import SUBSCRIPTION_PLANS, SubscriptionPlan

def test_subscription_plans_have_new_fields():
    for plan, details in SUBSCRIPTION_PLANS.items():
        assert hasattr(details, "daily_limit")
        assert hasattr(details, "validity_days")
        assert hasattr(details, "allowed_trainers")

def test_free_plan_specifics():
    free_plan = SUBSCRIPTION_PLANS[SubscriptionPlan.FREE]
    assert free_plan.daily_limit == 20
    assert free_plan.validity_days == 7
    assert free_plan.allowed_trainers == ["gymbro"]
    assert free_plan.total_limit is None
