from datetime import datetime, timedelta
from src.api.models.user_profile import UserProfile
from src.core.subscription import SubscriptionPlan


def test_pro_user_limits():
    # User with Pro plan
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="rafacolucci@gmail.com",
        subscription_plan=SubscriptionPlan.PRO,
        messages_sent_this_month=10,
        photos_sent_this_month=3,
    )

    assert profile.is_trial_active is False
    assert profile.current_daily_limit is None
    assert profile.current_plan_limit == 500
    assert profile.effective_remaining_messages == 490
    assert profile.effective_remaining_photos == 12
    assert profile.effective_chat_enabled is True
    assert profile.effective_plan_name == "Pro"


def test_pro_billing_cycle_reset():
    # User with Pro plan and 31 days since last cycle start.
    old_start = datetime.now() - timedelta(days=31)
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="rafacolucci@gmail.com",
        subscription_plan=SubscriptionPlan.PRO,
        messages_sent_this_month=500,
        photos_sent_this_month=15,
        current_billing_cycle_start=old_start,
    )

    assert profile.effective_remaining_messages == 500
    assert profile.effective_remaining_photos == 15

def test_free_user_with_active_trial_gets_pro_capabilities():
    trial_end = datetime.now() + timedelta(days=2)
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        trial_ends_at=trial_end,
        messages_sent_this_month=20,
        photos_sent_this_month=2,
    )

    assert profile.is_trial_active is True
    assert profile.effective_chat_enabled is True
    assert profile.current_plan_limit == 500
    assert profile.effective_remaining_messages == 480
    assert profile.effective_remaining_photos == 13
    assert profile.effective_plan_name == "Pro"


def test_free_post_trial_limits_are_blocked():
    trial_end = datetime.now() - timedelta(days=1)
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        trial_ends_at=trial_end,
    )

    assert profile.is_trial_active is False
    assert profile.effective_chat_enabled is False
    assert profile.current_plan_limit is None
    assert profile.effective_remaining_messages == 0
    assert profile.effective_remaining_photos == 0
    assert profile.effective_plan_name == "Free"
