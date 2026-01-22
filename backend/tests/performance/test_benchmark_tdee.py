
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta, datetime

from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog

def generate_mock_data(days: int = 365):
    """Generates consistent weight loss data."""
    start_date = date.today() - timedelta(days=days)
    weight_logs = []
    nutrition_logs = []
    
    current_weight = 100.0
    
    for i in range(days):
        d = start_date + timedelta(days=i)
        
        # Simulate slight weight noise and trend
        current_weight -= 0.05  # Losing weight
        noise = (i % 3) * 0.1
        
        weight_logs.append(
            WeightLog(
                user_email="bench@test.com",
                date=d,
                weight_kg=current_weight + noise,
                body_fat_pct=20.0
            )
        )
        
        nutrition_logs.append(
            NutritionLog(
                user_email="bench@test.com",
                date=datetime(d.year, d.month, d.day),
                calories=2500,
                protein_grams=200,
                carbs_grams=250,
                fat_grams=80,
                meals=[]
            )
        )
        
    return weight_logs, nutrition_logs

@pytest.fixture
def tdee_service():
    mock_db = MagicMock()
    # Profile mock
    mock_profile = MagicMock()
    mock_profile.weekly_rate = 0.5
    mock_profile.goal_type = "lose"
    mock_profile.target_weight = 80.0
    mock_db.get_user_profile.return_value = mock_profile
    
    service = AdaptiveTDEEService(mock_db)
    return service, mock_db

def test_benchmark_calculate_tdee(benchmark, tdee_service):
    service, mock_db = tdee_service
    weight_logs, nutrition_logs = generate_mock_data(365)
    
    # Setup mock returns
    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    
    # Run benchmark
    result = benchmark(service.calculate_tdee, "bench@test.com", lookback_weeks=3)
    
    # Verify correctness logic still holds (sanity check)
    assert result["tdee"] > 0
    assert result["confidence"] in ["high", "medium", "low"]
