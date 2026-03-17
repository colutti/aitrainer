import sys
import os
import json
from datetime import datetime, timezone, timedelta

# Add /app to path (in container /app is the backend dir)
sys.path.append("/app")

try:
    from src.core.deps import get_mongo_database
    from src.core.config import settings
    from src.api.models.user_profile import UserProfile
    import jwt
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def setup_e2e_user():
    email = "e2e-bot@fityq.it"
    # get_mongo_database returns the MongoDatabase service instance
    db_service = get_mongo_database()
    
    # Check if user exists using the service method
    user = db_service.get_user_profile(email)
    
    if not user:
        # Create user profile
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
            display_name="E2E Bot"
        )
        db_service.save_user_profile(user)
        print(f"DEBUG: Created new E2E bot user: {email}", file=sys.stderr)
    else:
        # Ensure onboarding is completed and it's a free plan
        db_service.update_user_profile_fields(email, {
            "onboarding_completed": True, 
            "subscription_plan": "Free", 
            "display_name": "E2E Bot"
        })
        print(f"DEBUG: Updated existing E2E bot user: {email}", file=sys.stderr)
        
    # Generate token using settings.SECRET_KEY
    payload = {"sub": email, "exp": datetime.now(timezone.utc) + timedelta(hours=24)}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    
    # Output to stdout
    print(json.dumps({
        "email": email,
        "token": token
    }))

if __name__ == "__main__":
    setup_e2e_user()
