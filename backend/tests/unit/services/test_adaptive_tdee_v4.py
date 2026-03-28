import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog

@pytest.fixture
def db_mock():
    db = MagicMock()
    return db

@pytest.fixture
def service(db_mock):
    return AdaptiveTDEEService(db_mock)

def _build_test_data(days, user_email="test@test.com", start_weight=80.0, weight_drop_per_day=0.0, calories=2000, skip_nutrition_days=None):
    weights = []
    nutrition = []
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    
    skip_nutrition_days = skip_nutrition_days or []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Weight Log (no gaps for now)
        weights.append(WeightLog(
            user_email=user_email,
            date=current_date,
            weight_kg=start_weight - (weight_drop_per_day * i)
        ))
        
        # Nutrition Log (with gaps)
        if i not in skip_nutrition_days:
            nutrition.append(NutritionLog(
                user_email=user_email,
                date=current_date,
                calories=calories,
                protein_grams=150,
                carbs_grams=200,
                fat_grams=60
            ))
            
    return weights, nutrition

class TestAdaptiveTDEEV4GapImputation:
    
    def test_gap_imputation_1_to_3_days_missing(self, service, db_mock):
        """
        If 1 to 3 days of nutrition are missing in a 7-day window, 
        the algorithm should impute the data and NOT return an empty observation list.
        Currently, compute_single_window_observation returns None if len(window_calories) < 4.
        """
        # Create 14 days of data. Skip nutrition on days 8, 9, 10 (3 days missing in the second week)
        weights, nutrition = _build_test_data(
            days=14, 
            weight_drop_per_day=0.1, 
            calories=2000, 
            skip_nutrition_days=[8, 9, 10]
        )
        
        # Calculate daily trend manually (mocking Step 4)
        daily_trend = {w.date: w.weight_kg for w in weights} # Perfect trend
        nutrition_by_date = {n.date: n.calories for n in nutrition}
        
        # Act
        observations = service.compute_tdee_observations(
            daily_trend=daily_trend,
            nutrition_by_date=nutrition_by_date,
            energy_per_kg=7700.0,
            daily_target_fallback=2000 # New parameter to be added
        )
        
        # Assert
        # With 14 days of data, we should have 8 observations (days 6 to 13)
        # Even with 3 days missing, imputation should save the window.
        assert len(observations) == 8
        
    def test_gap_imputation_extreme_gap_pauses_algorithm(self, service, db_mock):
        """
        If a gap is too large (e.g., > 10 days of no nutrition data), 
        the algorithm should not impute blindly and should pause (return empty or few observations).
        """
        # 21 days total. Miss 14 days in the middle.
        skip_days = list(range(5, 19))
        weights, nutrition = _build_test_data(
            days=21, 
            weight_drop_per_day=0.1, 
            calories=2000, 
            skip_nutrition_days=skip_days
        )
        
        daily_trend = {w.date: w.weight_kg for w in weights}
        nutrition_by_date = {n.date: n.calories for n in nutrition}
        
        # Act
        observations = service.compute_tdee_observations(
            daily_trend=daily_trend,
            nutrition_by_date=nutrition_by_date,
            energy_per_kg=7700.0,
            daily_target_fallback=2000
        )
        
        # Observations where window has 0 or 1 real data points out of 7 should be rejected.
        # So we expect very few or 0 observations in the middle.
        assert len(observations) < 10 # Should be severely penalized

class TestAdaptiveTDEEV4WaterWeightDampening:
    def test_water_weight_swoosh_dampening(self, service):
        """
        If a user loses weight very rapidly in the first week (>1% per week equivalent), 
        energy_per_kg should be dampened (e.g. 2000-3000) to avoid artificial TDEE spikes.
        """
        # slope is kg/day. -0.5 kg/day is -3.5kg/week (extreme water loss)
        energy = service.estimate_energy_per_kg(body_fat_pct=None, slope=-0.5)
        
        # Original default was ~7700. With dampening, it should drop significantly.
        assert energy < 5000, f"Expected dampened energy per kg, got {energy}"

    def test_normal_weight_loss_no_dampening(self, service):
        """
        If a user loses weight normally (e.g. 0.5kg/week), 
        energy_per_kg should remain close to the physiological fat/lean mix (~7700).
        """
        # slope is kg/day. -0.07 kg/day is ~0.49kg/week (normal)
        energy = service.estimate_energy_per_kg(body_fat_pct=None, slope=-0.07)
        
        assert 7000 < energy < 8000, f"Expected normal energy per kg, got {energy}"

class TestAdaptiveTDEEV4DynamicSpan:
    def test_dynamic_span_smooth_data_low_variance(self, service):
        """
        If weight drops consistently every day with minimal noise, the variance is low.
        The algorithm should reduce the EMA span (e.g. to ~7-10 days) to respond quickly.
        """
        weights, _ = _build_test_data(days=14, weight_drop_per_day=0.1) # Perfectly linear
        
        # We need a method to calculate dynamic span
        span = service._calculate_dynamic_span(weights)
        
        # It should be close to the minimum span because it's a perfect line
        assert span < 14, f"Expected low span for smooth data, got {span}"

    def test_dynamic_span_noisy_data_high_variance(self, service):
        """
        If weight fluctuates wildly (high variance from trend), the algorithm should 
        increase the EMA span (e.g. to ~21-30 days) to avoid overreacting to noise.
        """
        weights, _ = _build_test_data(days=14, weight_drop_per_day=0.1)
        # Introduce wild noise (± 1.5kg every other day)
        for i, w in enumerate(weights):
            if i % 2 == 0:
                w.weight_kg += 1.5
            else:
                w.weight_kg -= 1.5
                
        span = service._calculate_dynamic_span(weights)
        
        # It should be close to the maximum span because of high noise
        assert span >= 21, f"Expected high span for noisy data, got {span}"

class TestAdaptiveTDEEV4EdgeCases:
    def test_numpy_regression_fallback(self, service):
        """
        If numpy polyfit throws an exception (e.g. RankWarning) or std is 0,
        the fallback linear calculation should handle it.
        """
        # Create identical weights (std = 0)
        weights, _ = _build_test_data(days=5, weight_drop_per_day=0.0)
        
        m, c, r_val = service._calculate_regression_trend(weights)
        
        # Slope should be 0, correlation should be 0 because std is 0
        assert m == pytest.approx(0.0, abs=1e-10)
        assert r_val == 0.0
        assert c == pytest.approx(80.0, abs=1e-10) # initial weight

    def test_regression_with_empty_logs(self, service):
        m, c, r_val = service._calculate_regression_trend([])
        assert m == 0.0
        assert c == 0.0
        assert r_val == 0.0

    def test_regression_single_log(self, service):
        weights, _ = _build_test_data(days=1, weight_drop_per_day=0.0)
        m, c, r_val = service._calculate_regression_trend(weights)
        assert m == 0.0
        assert c == 80.0
        assert r_val == 0.0
