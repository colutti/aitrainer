from src.api.models.user_profile import UserProfile

def test_user_profile_has_tdee_start_date():
    profile = UserProfile(gender="Masculino", age=30, height=180, goal_type="maintain", email="test@example.com")
    assert hasattr(profile, "tdee_start_date")
    assert profile.tdee_start_date is None

def test_user_profile_accepts_tdee_start_date():
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="test@example.com", 
        tdee_start_date="2026-03-06"
    )
    assert profile.tdee_start_date == "2026-03-06"
