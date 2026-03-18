from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain, get_mongo_database
from src.api.models.user_profile import UserProfile

client = TestClient(app)

def test_user_settings_operations():
    """
    Test retrieving and updating user profile and identity using direct overrides.
    """
    user_email = "test@example.com"
    mock_brain = MagicMock()
    mock_db = MagicMock()
    
    # Overrides
    app.dependency_overrides[verify_token] = lambda: user_email
    app.dependency_overrides[get_ai_trainer_brain] = lambda: mock_brain
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    
    try:
        # 1. Get Profile
        mock_profile = UserProfile(
            email=user_email,
            gender="Masculino",
            age=30,
            weight=70.0,
            height=170,
            goal_type="maintain",
            subscription_plan="Free",
            display_name="Original Name",
            onboarding_completed=True
        )
        mock_brain.get_user_profile.return_value = mock_profile
        
        response = client.get("/user/profile")
        assert response.status_code == 200
        assert response.json()["display_name"] == "Original Name"
        
        # 2. Update Profile
        update_payload = {
            "gender": "Feminino",
            "age": 31,
            "weight": 68.0,
            "height": 170,
            "goal_type": "lose",
            "weekly_rate": 0.5
        }
        
        update_response = client.post("/user/update_profile", json=update_payload)
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "Profile updated successfully"
        mock_brain.save_user_profile.assert_called()
        
        # 3. Update Identity
        identity_payload = {
            "display_name": "Updated Name"
        }
        
        identity_response = client.post("/user/update_identity", json=identity_payload)
        assert identity_response.status_code == 200
        assert identity_response.json()["message"] == "Identity updated successfully"
        mock_brain.update_user_profile_fields.assert_called_with(user_email, {"display_name": "Updated Name"})
        
    finally:
        app.dependency_overrides.clear()
