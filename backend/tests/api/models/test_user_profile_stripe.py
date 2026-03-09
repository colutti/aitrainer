from src.api.models.user_profile import UserProfile

def test_user_profile_accepts_stripe_fields():
    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        weight=70.0,
        height=170,
        goal_type="maintain",
        weekly_rate=0.5,
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
        stripe_subscription_status="active"
    )
    assert profile.stripe_customer_id == "cus_123"
    assert profile.stripe_subscription_status == "active"
