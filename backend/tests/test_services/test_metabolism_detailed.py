
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

def test_scenario_loss(service, mock_db):
    """
    Scenario: Weight Loss
    85.0kg -> 83.0kg in 20 days (21 logs).
    Loss: 2.0kg.
    Avg Intake: 2200 kcal.
    Daily Deficit: (2.0 * 7700) / 20 = 770 kcal.
    Theoretical TDEE: 2200 + 770 = 2970 kcal.
    """
    today = date.today()
    start_date = today - timedelta(days=20)
    days = 21
    
    weights = []
    for i in range(days):
        w = 85.0 - (2.0 * i / (days - 1))
        weights.append(WeightLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), weight_kg=w))
        
    nutrition = [NutritionLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), calories=2200, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(days)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = None # Maintenance goal

    result = service.calculate_tdee("demo@demo.com", lookback_weeks=3)
    
    # Current EMA logic with alpha=0.1 calculates ~2627 (343kcal error)
    # Target Regression logic should be +/- 50kcal of 2970
    print(f"Calculated TDEE (Loss): {result['tdee']}")
    assert abs(result["tdee"] - 2970) < 50

def test_scenario_gain(service, mock_db):
    """
    Scenario: Weight Gain
    80.0kg -> 82.0kg in 20 days.
    Gain: 2.0kg.
    Avg Intake: 3000 kcal.
    Daily Surplus: (2.0 * 7700) / 20 = 770 kcal.
    Theoretical TDEE: 3000 - 770 = 2230 kcal.
    """
    today = date.today()
    start_date = today - timedelta(days=20)
    days = 21
    
    weights = []
    for i in range(days):
        w = 80.0 + (2.0 * i / (days - 1))
        weights.append(WeightLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), weight_kg=w))
        
    nutrition = [NutritionLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), calories=3000, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(days)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = None

    result = service.calculate_tdee("demo@demo.com", lookback_weeks=3)
    
    print(f"Calculated TDEE (Gain): {result['tdee']}")
    assert abs(result["tdee"] - 2230) < 50

def test_scenario_maintenance(service, mock_db):
    """
    Scenario: Maintenance
    70.0kg stable for 20 days.
    Avg Intake: 2500 kcal.
    Theoretical TDEE: 2500 kcal.
    """
    today = date.today()
    start_date = today - timedelta(days=20)
    days = 21
    
    weights = [WeightLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), weight_kg=70.0) for i in range(days)]
    nutrition = [NutritionLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(days)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = None

    result = service.calculate_tdee("demo@demo.com", lookback_weeks=3)
    
    assert abs(result["tdee"] - 2500) < 10

def test_scenario_noisy_maintenance(service, mock_db):
    """
    Scenario: Noisy Maintenance
    70.0kg +/- 0.4kg fluctuations.
    Avg Intake: 2500 kcal.
    Theoretical TDEE: 2500 kcal.
    """
    today = date.today()
    start_date = today - timedelta(days=20)
    days = 21
    
    # 70.0, 70.4, 69.6, 70.0 ...
    modifiers = [0, 0.4, -0.4, 0, 0.2, -0.2, 0.1, -0.1, 0, 0.3, -0.3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    weights = [WeightLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), weight_kg=70.0 + modifiers[i]) for i in range(days)]
    nutrition = [NutritionLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), calories=2500, protein_grams = 150, carbs_grams = 250, fat_grams = 80) for i in range(days)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = None

    result = service.calculate_tdee("demo@demo.com", lookback_weeks=3)
    
    # Simple endpoint delta (last - first) would see 70.0 - 70.0 = 0.
    # Linear regression should also find slope near 0.
    assert abs(result["tdee"] - 2500) < 50

def test_scenario_missing_data(service, mock_db):
    """
    Scenario: Missing Data
    Weight logs every 4 days.
    80.0 -> 79.0 in 20 days.
    Intake: 2000 kcal.
    Daily Deficit: (1.0 * 7700) / 20 = 385.
    Theoretical TDEE: 2000 + 385 = 2385.
    """
    today = date.today()
    start_date = today - timedelta(days=20)
    
    weights = []
    for i in range(0, 21, 4): # Day 0, 4, 8, 12, 16, 20
        w = 80.0 - (1.0 * i / 20)
        weights.append(WeightLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), weight_kg=w))
        
    nutrition = [NutritionLog(user_email="demo@demo.com", date=start_date + timedelta(days=i), calories=2000, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(21)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = None

    result = service.calculate_tdee("demo@demo.com", lookback_weeks=3)
    
    assert abs(result["tdee"] - 2385) < 50
