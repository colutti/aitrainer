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
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.5
    mock_db.get_user_profile.return_value = profile_mock
    
    targets = service.get_current_targets("test@test.com")
    
    # Target = 2500 - (0.5 * 1100) = 2500 - 550 = 1950
    assert targets["tdee"] == 2500
    assert targets["daily_target"] == 1950
    assert "lose" in targets["reason"]

def test_get_current_targets_gain(service, mock_db):
    # Mock TDEE calculation
    service.calculate_tdee = MagicMock(return_value={"tdee": 2500, "confidence": "high"})
    
    # Mock Profile
    profile_mock = MagicMock()
    profile_mock.goal_type = "gain"
    profile_mock.weekly_rate = 0.2
    
    mock_db.get_user_profile.return_value = profile_mock
    
    targets = service.get_current_targets("test@test.com")
    
    # Target = 2500 + (0.2 * 1100) = 2500 + 220 = 2720
    assert targets["tdee"] == 2500
    assert targets["daily_target"] == 2720

def test_tdee_includes_body_composition_changes(service, mock_db):
    """TDEE includes fat/lean change when composition data available."""
    today = date.today()
    start_date = today - timedelta(days=20)
    
    # Weight drops 80 -> 78 (2kg loss)
    # Fat drops 25% -> 23%
    # Start Fat Mass = 80 * 0.25 = 20kg
    # End Fat Mass = 78 * 0.23 = 17.94kg
    # Fat Change = -2.06kg
    # Total Change = -2.0kg
    # Lean Change = -2.0 - (-2.06) = +0.06kg (Muscle gain!)
    
    weights = []
    # Create start log
    weights.append(WeightLog(
        user_email="comp@test.com", 
        date=start_date, 
        weight_kg=80.0, 
        body_fat_pct=25.0
    ))
    # Create filler logs (composition not strictly needed for fillers in current logic unless we checked every log)
    # The new logic only checks first and last valid logs.
    for i in range(1, 20):
        weights.append(WeightLog(
            user_email="comp@test.com", 
            date=start_date + timedelta(days=i), 
            weight_kg=80.0 - (2.0 * i / 20)
        ))
    # Create end log
    weights.append(WeightLog(
        user_email="comp@test.com", 
        date=today, 
        weight_kg=78.0, 
        body_fat_pct=23.0
    ))
    
    # Nutrition logs (needed to pass MIN_DATA_DAYS check)
    nutrition = [NutritionLog(user_email="comp@test.com", date=start_date + timedelta(days=i), calories=2000, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(21)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("comp@test.com", lookback_weeks=3)
    
    assert "fat_change_kg" in result
    assert result["fat_change_kg"] == -2.06
    assert result["lean_change_kg"] == 0.06
    assert result["start_fat_pct"] == 25.0
    assert result["end_fat_pct"] == 23.0

def test_tdee_outlier_filtering(service, mock_db):
    """Verify that outliers are filtered and counted."""
    today = date.today()
    start_date = today - timedelta(days=20)
    
    # 21 days of data with one spike
    weights = []
    for i in range(21):
        weight = 70.0
        if i == 10: # Spike!
            weight = 75.0
        weights.append(WeightLog(user_email="test@test.com", date=start_date + timedelta(days=i), weight_kg=weight))
    
    nutrition = [NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(21)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    assert result["outliers_count"] == 1
    assert result["weight_logs_count"] == 20 # 21 total - 1 outlier
    assert result["tdee"] == 2500 # Should ignore the spike

def test_tdee_sparse_weight_logs(service, mock_db):
    """Verify separate counts for weight and nutrition logs."""
    today = date.today()
    start_date = today - timedelta(days=20)
    
    # 21 days of nutrition logs (Dense)
    nutrition = [
        NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) 
        for i in range(21)
    ]
    
    # Only 3 weight logs (Sparse)
    weights = [
        WeightLog(user_email="test@test.com", date=start_date, weight_kg=70.0),
        WeightLog(user_email="test@test.com", date=start_date + timedelta(days=10), weight_kg=70.0),
        WeightLog(user_email="test@test.com", date=start_date + timedelta(days=20), weight_kg=70.0)
    ]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    # Check distinct counters
    assert result["weight_logs_count"] == 3
    assert result["nutrition_logs_count"] == 21
    # Confidence might be low/medium due to sparse weight data, but that's a separate check

def test_tdee_confidence_reason(service, mock_db):
    """Verify confidence reason is returned."""
    today = date.today()
    start_date = today - timedelta(days=20)
    
    # Excellent data
    weights = [WeightLog(user_email="test@test.com", date=start_date + timedelta(days=i), weight_kg=70.0) for i in range(21)]
    nutrition = [NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) for i in range(21)]
    
    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    
    result = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    assert result["confidence"] == "high"
    assert "Excelente" in result["confidence_reason"]
    
    # Poor nutrition data (just enough to calculate, but bad adherence)
    # 8 logs out of 21 days = ~38% adherence (< 60%)
    nutrition_poor = [
        NutritionLog(user_email="test@test.com", date=start_date + timedelta(days=i), calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80) 
        for i in range(8)
    ]
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_poor
    
    result_poor = service.calculate_tdee("test@test.com", lookback_weeks=3)
    
    assert result_poor["confidence"] == "low"
    assert "Muitos dias sem registro" in result_poor["confidence_reason"]
