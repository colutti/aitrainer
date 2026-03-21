from datetime import datetime, timedelta
from src.api.models.user_profile import UserProfile
from src.core.subscription import SubscriptionPlan, SUBSCRIPTION_PLANS

def test_premium_user_limits():
    # User with Premium plan
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="rafacolucci@gmail.com",
        subscription_plan=SubscriptionPlan.PREMIUM,
        messages_sent_this_month=1
    )
    
    # Check current_daily_limit (this is what the UI currently uses)
    # It returns None for Premium because it only has a monthly limit
    assert profile.current_daily_limit is None
    
    # Check current_plan_limit (this is what the UI should use)
    # Premium monthly limit is 1000.
    assert profile.current_plan_limit == 1000
    
    # Check effective_remaining_messages
    # Premium monthly limit is 1000. 1000 - 1 = 999.
    assert profile.effective_remaining_messages == 999

def test_premium_billing_cycle_reset():
    # User with Premium plan and 31 days since last cycle start
    old_start = datetime.now() - timedelta(days=31)
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="rafacolucci@gmail.com",
        subscription_plan=SubscriptionPlan.PREMIUM,
        messages_sent_this_month=500,
        current_billing_cycle_start=old_start
    )
    
    # effective_remaining_messages should be 1000 because cycle reset
    assert profile.effective_remaining_messages == 1000

def test_free_user_limits():
    # User with Free plan
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        messages_sent_today=5,
        last_message_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Check current_daily_limit
    # Free daily limit is 20.
    assert profile.current_daily_limit == 20
    assert profile.current_plan_limit == 20
    
    # Check effective_remaining_messages
    # 20 - 5 = 15
    assert profile.effective_remaining_messages == 15

def test_free_daily_reset():
    # User with Free plan and last message yesterday
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="free@example.com",
        subscription_plan=SubscriptionPlan.FREE,
        messages_sent_today=5,
        last_message_date=yesterday
    )
    
    # effective_remaining_messages should be 20 because daily reset
    assert profile.effective_remaining_messages == 20
