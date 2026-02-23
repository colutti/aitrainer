"""Test TDEE activity factor retrieval from profile."""
from datetime import date, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.user_profile import UserProfile
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog


def test_calculate_tdee_uses_profile_activity_factor():
    """Test that TDEE calculation uses activity_factor from profile if set."""
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.2,
    )

    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=20),
            weight_kg=80.0,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=10),
            weight_kg=79.5,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=79.0,
            bmr=1700,
        ),
    ]

    nutrition_logs = [
        NutritionLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=i),
            calories=1800,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
            partial_logged=False,
        )
        for i in range(20)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile
    mock_db.update_user_coaching_target = MagicMock()

    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    expected_prior = 1700 * 1.2
    assert result["tdee"] > 0
    assert abs(result["tdee"] - expected_prior) < 300


def test_calculate_tdee_uses_default_activity_factor_when_none():
    """Test that TDEE calculation falls back to 1.45 when activity_factor is None."""
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=None,
    )

    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=20),
            weight_kg=80.0,
            bmr=1700,
        ),
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=79.5,
            bmr=1700,
        ),
    ]

    nutrition_logs = [
        NutritionLog(
            user_email="test@example.com",
            date=date.today() - timedelta(days=i),
            calories=2465,  # 1700 * 1.45 (default activity factor)
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
            partial_logged=False,
        )
        for i in range(20)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile
    mock_db.update_user_coaching_target = MagicMock()

    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    # When profile.tdee_activity_factor is None, should use default 1.45
    assert result["tdee"] > 0


def test_calculate_fallback_tdee_uses_profile_activity_factor():
    """Test that fallback TDEE also respects activity_factor."""
    mock_db = MagicMock()
    service = AdaptiveTDEEService(mock_db)

    profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.725,
    )

    weight_logs = [
        WeightLog(
            user_email="test@example.com",
            date=date.today(),
            weight_kg=80.0,
            bmr=1700,
        ),
    ]
    nutrition_logs = []

    mock_db.get_weight_logs_by_date_range.return_value = weight_logs
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
    mock_db.get_user_profile.return_value = profile

    result = service.calculate_tdee("test@example.com", lookback_weeks=4)

    expected = 1700 * 1.725
    assert result["tdee"] > 0
    assert abs(result["tdee"] - expected) < 100
