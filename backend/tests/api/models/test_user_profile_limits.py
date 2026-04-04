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
        messages_sent_this_month=1,
    )

    # It returns None for Pro because it only has a monthly limit.
    assert profile.current_daily_limit is None
    assert profile.current_plan_limit == 300
    assert profile.effective_remaining_messages == 299


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
        current_billing_cycle_start=old_start,
    )

    # effective_remaining_messages should be 300 because cycle reset.
    assert profile.effective_remaining_messages == 300

def test_free_user_limits():
    # User with Free plan.
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        messages_sent_today=5,
        last_message_date=datetime.now().strftime("%Y-%m-%d"),
    )

    # Free daily limit is 20.
    assert profile.current_daily_limit == 20
    assert profile.current_plan_limit == 20

    # 20 - 5 = 15
    assert profile.effective_remaining_messages == 15


def test_free_daily_reset():
    # User with Free plan and last message yesterday.
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="maintain",
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        messages_sent_today=5,
        last_message_date=yesterday,
    )

    # effective_remaining_messages should be 20 because daily reset.
    assert profile.effective_remaining_messages == 20
