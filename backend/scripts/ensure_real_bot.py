import sys
import os

# Add /app to path (in container /app is the backend dir)
sys.path.append("/app")

try:
    from src.core.deps import get_mongo_database
    from src.api.models.user_profile import UserProfile
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def ensure_real_bot():
    email = "bot-real@fityq.it"
    db_service = get_mongo_database()
    
    user = db_service.get_user_profile(email)
    
    if not user:
        user = UserProfile(
            email=email,
            gender="Masculino",
            age=30,
            weight=80.0,
            height=180,
            goal_type="maintain",
            onboarding_completed=True,
            subscription_plan="Free",
            role="user",
            display_name="Real QA Bot"
        )
        db_service.save_user_profile(user)
        print(f"Created real QA bot user profile: {email}")
    else:
        print(f"Real QA bot user profile already exists: {email}")

if __name__ == "__main__":
    ensure_real_bot()
