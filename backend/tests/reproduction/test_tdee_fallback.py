from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog

@pytest.fixture
def service():
    db = MagicMock()
    return AdaptiveTDEEService(db)

def test_tdee_fallback_on_insufficient_data(service):
    """
    Test that TDEE is not 0 even with insufficient data.
    It should fallback to a BMR-based estimate.
    """
    user_email = "test@example.com"
    
    # 1. Setup Data: only 2 days of logs (less than MIN_DATA_DAYS=7)
    today = date.today()
    log1 = WeightLog(user_email=user_email, date=today - timedelta(days=1), weight_kg=80.0, bmr=1800)
    log2 = WeightLog(user_email=user_email, date=today, weight_kg=80.0, bmr=1800)
    
    service.db.get_weight_logs_by_date_range.return_value = [log1, log2]
    service.db.get_nutrition_logs_by_date_range.return_value = []
    service.db.get_user_profile.return_value = None # No profile for now
    
    # 2. ACT
    result = service.calculate_tdee(user_email)
    
    # 3. ASSERT
    # Current behavior: returns 0
    # Desired behavior: returns at least BMR or calculated fallback
    assert result["tdee"] > 0, f"Expected TDEE > 0, got {result['tdee']}"
    assert result["daily_target"] > 0
    assert result["confidence"] == "none" # Still low confidence as it is fallback
    assert "estimativa" in result.get("confidence_reason", "").lower()
