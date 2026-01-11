import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def service(mock_db):
    return AdaptiveTDEEService(mock_db)

def test_tdee_insufficient_data(service, mock_db):
    mock_db.get_weight_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs_by_date_range.return_value = []
    
    result = service.calculate_tdee("test@test.com")
    
    assert result["tdee"] == 0
    assert result["confidence"] == "none"

def test_tdee_calculation_maintenance(service, mock_db):
    # User maintains weight with constant calories
    today = date.today()
    start_date = today - timedelta(days=20)
    
    # 21 days of data
    weights = [WeightLog(user_email="test@test.com", date=start_date + timedelta(days=i), weight_kg=70.0) for i in range(21)]
    # 21 days of nutrition at 2500 kcal
    nutrition = [NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(21)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    # Weight change = 0, so TDEE should equal Avg Calories
    assert result["tdee"] == 2500
    assert result["avg_calories"] == 2500
    assert result["weight_change_per_week"] == 0.0
    assert result["confidence"] == "high" # High adherence

def test_tdee_calculation_losing_weight(service, mock_db):
    # User loses 1kg over 20 days eating 2000 kcal
    # 1kg fat = 7700 kcal deficit total
    # Daily deficit = 7700 / 20 = 385 kcal
    # TDEE should be ~ 2000 + 385 = 2385
    
    today = date.today()
    start_date = today - timedelta(days=20)
    days = 21
    
    # Weight drops from 81.0 to 80.0 linearly
    weights = []
    for i in range(days):
        w = 81.0 - (1.0 * i / (days - 1))
        weights.append(WeightLog(user_email="test@test.com", date=start_date + timedelta(days=i), weight_kg=w))
        
    nutrition = [NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2000, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(days)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    # TDEE approx 2385 if raw. EMA smoothing (alpha=0.1) causes lag, so the estimated weight loss 
    # will be less than raw, resulting in a lower TDEE estimate.
    # We accept a value closer to 2200-2400.
    assert 2200 < result["tdee"] < 2420
    assert result["avg_calories"] == 2000
    assert result["weight_change_per_week"] < 0
    
def test_insufficient_nutrition_logs(service, mock_db):
    # Enough weight data, but only 2 nutrition logs
    today = date.today()
    start_date = today - timedelta(days=20)
    
    weights = [WeightLog(user_email="test@test.com", date=start_date + timedelta(days=i), weight_kg=70.0) for i in range(21)]
    nutrition = [NutritionLog(user_email="test@test.com", date=start_date, calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80)] # Just 1 log
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("test@test.com")
    
    assert result["tdee"] == 0
    assert result["confidence"] == "none"

def test_get_current_targets(service, mock_db):
    # Mock TDEE calculation
    service.calculate_tdee = MagicMock(return_value={"tdee": 2500, "confidence": "high"})
    
    # Mock Profile
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose_weight"
    profile_mock.weekly_rate = 0.5
    mock_db.get_user_profile.return_value = profile_mock
    
    targets = service.get_current_targets("test@test.com")
    
    # Target = 2500 - (0.5 * 1100) = 2500 - 550 = 1950
    assert targets["tdee"] == 2500
    assert targets["daily_target"] == 1950
    assert "lose_weight" in targets["reason"]

def test_get_current_targets_gain(service, mock_db):
    # Mock TDEE calculation
    service.calculate_tdee = MagicMock(return_value={"tdee": 2500, "confidence": "high"})
    
    # Mock Profile
    profile_mock = MagicMock()
    profile_mock.goal_type = "gain_muscle"
    profile_mock.weekly_rate = 0.2
    
    mock_db.get_user_profile.return_value = profile_mock
    
    targets = service.get_current_targets("test@test.com")
    
    # Target = 2500 + (0.2 * 1100) = 2500 + 220 = 2720
    assert targets["tdee"] == 2500
    assert targets["daily_target"] == 2720
