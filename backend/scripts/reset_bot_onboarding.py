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

def reset_bot_for_onboarding():
    email = "bot-real@fityq.it"
    db_service = get_mongo_database()
    
    user = db_service.get_user_profile(email)
    
    # Se o usuário não existir, cria um novo. Se existir, reseta o onboarding.
    if not user:
        user = UserProfile(
            email=email,
            gender="Masculino",
            age=30,
            weight=80.0,
            height=180,
            goal_type="maintain",
            onboarding_completed=False, # FORÇAR WIZARD
            subscription_plan="Free",
            role="user",
            display_name="Real QA Bot"
        )
        db_service.save_user_profile(user)
        print(f"Created real QA bot user profile: {email}")
    else:
        # Resetar apenas os campos necessários para o wizard aparecer
        user.onboarding_completed = False
        db_service.save_user_profile(user)
        print(f"Reset onboarding for existing bot user: {email}")

if __name__ == "__main__":
    reset_bot_for_onboarding()
