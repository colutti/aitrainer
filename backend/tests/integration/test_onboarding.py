from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.api.main import app
from src.services.auth import verify_token

client = TestClient(app)

def test_onboarding_profile_completes_successfully():
    """
    Test that an authenticated user can complete their profile onboarding.
    """
    user_email = "test@example.com"
    # Mock authentication
    app.dependency_overrides[verify_token] = lambda: user_email
    
    with patch("src.api.endpoints.onboarding.get_mongo_database") as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        
        # Mock existing profile
        from src.api.models.user_profile import UserProfile
        mock_profile = UserProfile(
            email=user_email,
            gender="Male",
            age=25,
            weight=70.0,
            height=170,
            goal_type="maintain",
            onboarding_completed=False
        )
        mock_db.get_user_profile.return_value = mock_profile
        
        payload = {
            "gender": "Masculino",
            "age": 30,
            "weight": 75.0,
            "height": 180,
            "goal_type": "maintain",
            "weekly_rate": 0.5,
            "trainer_type": "atlas",
            "subscription_plan": "Free",
            "name": "Test User"
        }
        
        response = client.post("/onboarding/profile", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        
        # Verify database calls
        mock_db.save_user_profile.assert_called_once()
        updated_profile = mock_db.save_user_profile.call_args[0][0]
        assert updated_profile.onboarding_completed is True
        assert updated_profile.display_name == "Test User"
        
        mock_db.save_trainer_profile.assert_called_once()
        
    app.dependency_overrides.clear()
