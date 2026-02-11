from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.models.weight_log import WeightLog
from src.core.deps import get_mongo_database
from src.services.auth import verify_token

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_body_composition_persistence_on_dashboard(client, mock_db):
    """
    Test that BF%, Muscle%, and BMR are pulled from history 
    if the latest log doesn't have them.
    """
    email = "test@example.com"
    
    # Yesterday's log with full composition
    yesterday = datetime(2026, 2, 8)
    log_yesterday = WeightLog(
        user_email=email,
        date=yesterday.date(),
        weight_kg=80.0,
        body_fat_pct=15.0,
        muscle_mass_pct=40.0,
        bmr=1800
    )
    
    # Today's log with only weight
    today = datetime(2026, 2, 9)
    log_today = WeightLog(
        user_email=email,
        date=today.date(),
        weight_kg=81.0,
        body_fat_pct=None,
        muscle_mass_pct=None,
        bmr=None
    )
    
    # Return logs in descending order (latest first)
    mock_db.get_weight_logs.return_value = [log_today, log_yesterday]
    mock_db.get_weight_logs_by_date_range.return_value = [log_today, log_yesterday]
    
    # Stub other methods to avoid crashes
    mock_db.get_nutrition_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs.return_value = []
    mock_db.get_workout_logs.return_value = []
    mock_db.get_user_profile.return_value = None
    
    # Mocking WorkoutRepository within the endpoint
    with patch('src.api.endpoints.dashboard.WorkoutRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_stats.return_value = MagicMock(
            current_streak_weeks=0, 
            recent_prs=[], 
            strength_radar={}, 
            volume_trend=[], 
            weekly_frequency=[],
            last_workout=None
        )
        
        # ACT
        response = client.get("/dashboard")
            
        # ASSERT
        assert response.status_code == 200
        data = response.json()
        body = data["stats"]["body"]
        
        # Desired behavior: should use 15.0, 40.0, 1800 from yesterday
        assert body["body_fat_pct"] == 15.0
        assert body["muscle_mass_pct"] == 40.0
        assert body["bmr"] == 1800
