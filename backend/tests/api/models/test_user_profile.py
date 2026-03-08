from src.api.models.user_profile import UserProfile

def test_user_profile_has_subscription_fields():
    profile = UserProfile(gender="Masculino", age=30, height=180, goal_type="maintain", email="test@example.com")
    assert hasattr(profile, "messages_sent_today")
    assert hasattr(profile, "last_message_date")
    assert profile.messages_sent_today == 0
    assert profile.last_message_date is None

def test_user_profile_accepts_subscription_fields():
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="test@example.com", 
        messages_sent_today=5,
        last_message_date="2026-03-08"
    )
    assert profile.messages_sent_today == 5
    assert profile.last_message_date == "2026-03-08"
