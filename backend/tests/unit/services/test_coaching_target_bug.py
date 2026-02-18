"""
Test to reproduce the bug: daily_target always equals TDEE regardless of goal.
Also test the macro calculation bug where macros exceed calorie target.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.user_profile import UserProfile


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def service(mock_db):
    return AdaptiveTDEEService(mock_db)


def test_coaching_target_lose_weight_goal(service, mock_db):
    """
    BUG REPRODUCTION:
    User has goal_type='lose' with weekly_rate=0.5kg
    Expected: daily_target should be LESS than TDEE (to create deficit)
    Actual: daily_target equals TDEE
    """
    today = date.today()
    start_date = today - timedelta(days=20)

    # Setup: User maintaining weight at 2500 kcal
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=80.0,
        )
        for i in range(21)
    ]

    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2500,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(21)
    ]

    # Mock profile: User wants to LOSE weight at 0.5kg/week
    profile = UserProfile(
        email="test@test.com",
        password_hash="hash",
        goal_type="lose",
        weekly_rate=0.5,
        gender="Masculino",
        age=30,
        weight=80.0,
        height=180,
    )

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    tdee = result["tdee"]
    daily_target = result["daily_target"]

    # ASSERTION: daily_target should be LESS than TDEE for weight loss
    # (deficit of ~550 kcal/day for 0.5kg/week loss)
    assert daily_target < tdee, (
        f"BUG: daily_target ({daily_target}) should be < TDEE ({tdee}) "
        f"for weight loss goal. Got difference: {daily_target - tdee}"
    )
    assert daily_target >= 1000, "daily_target should respect MIN_TDEE"


def test_coaching_target_gain_weight_goal(service, mock_db):
    """
    BUG REPRODUCTION:
    User has goal_type='gain' with weekly_rate=0.5kg
    Expected: daily_target should be MORE than TDEE (to create surplus)
    Actual: daily_target equals TDEE
    """
    today = date.today()
    start_date = today - timedelta(days=20)

    # Setup: User maintaining weight at 2500 kcal
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=80.0,
        )
        for i in range(21)
    ]

    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2500,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(21)
    ]

    # Mock profile: User wants to GAIN weight at 0.5kg/week
    profile = UserProfile(
        email="test@test.com",
        password_hash="hash",
        goal_type="gain",
        weekly_rate=0.5,
        gender="Masculino",
        age=30,
        weight=80.0,
        height=180,
    )

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    tdee = result["tdee"]
    daily_target = result["daily_target"]

    # ASSERTION: daily_target should be MORE than TDEE for weight gain
    # (surplus of ~550 kcal/day for 0.5kg/week gain)
    assert daily_target > tdee, (
        f"BUG: daily_target ({daily_target}) should be > TDEE ({tdee}) "
        f"for weight gain goal. Got difference: {daily_target - tdee}"
    )


def test_macro_targets_validate_total_calories(service, mock_db):
    """
    BUG REPRODUCTION:
    Macro targets (protein + fat + carbs) should sum to daily_target calories
    Expected: protein*4 + carbs*4 + fat*9 = daily_target ± small rounding error
    Actual: Macros exceed calorie target when daily_target is too low
    """
    # Test various daily_targets to find breaking point
    test_cases = [
        (80, 1000),  # Low weight, very low calories - likely to break
        (80, 1500),  # Low weight, low calories
        (100, 2000),  # Normal
        (120, 3000),  # Higher
    ]

    for weight_kg, daily_target in test_cases:
        macros = service._calculate_macro_targets(daily_target, weight_kg)

        protein_kcal = macros["protein"] * 4
        carbs_kcal = macros["carbs"] * 4
        fat_kcal = macros["fat"] * 9
        total_macros_kcal = protein_kcal + carbs_kcal + fat_kcal

        # ASSERTION: Total macro calories should not exceed daily_target by more than 10%
        # (to account for rounding)
        assert (
            total_macros_kcal <= daily_target * 1.1
        ), f"Macros exceed target: weight={weight_kg}kg, target={daily_target}kcal, macros={total_macros_kcal}kcal"

        # ASSERTION: Total macro calories should not be significantly less
        # (allow 5% slack for rounding)
        assert (
            total_macros_kcal >= daily_target * 0.95
        ), f"Macros too low: weight={weight_kg}kg, target={daily_target}kcal, macros={total_macros_kcal}kcal"


def test_macro_targets_detail(service):
    """
    Detailed test of macro calculation bug.
    Shows the exact problem when daily_target < protein_kcal + fat_kcal
    """
    # Scenario that triggers the bug
    daily_target = 1500  # Too low
    weight_kg = 100  # High weight = high protein requirement

    macros = service._calculate_macro_targets(daily_target, weight_kg)

    protein_kcal = macros["protein"] * 4
    fat_kcal = macros["fat"] * 9
    carbs_kcal = macros["carbs"] * 4

    total_kcal = protein_kcal + fat_kcal + carbs_kcal

    print(f"\n--- Macro Calculation Bug Example ---")
    print(f"Daily Target: {daily_target} kcal")
    print(f"Weight: {weight_kg} kg")
    print(f"Protein: {macros['protein']}g = {protein_kcal} kcal")
    print(f"Fat: {macros['fat']}g = {fat_kcal} kcal")
    print(f"Carbs: {macros['carbs']}g = {carbs_kcal} kcal")
    print(f"Total: {total_kcal} kcal")
    print(f"Difference from target: {total_kcal - daily_target} kcal")

    # The bug is revealed here
    if protein_kcal + fat_kcal > daily_target:
        assert macros["carbs"] == 0, "Carbs should be 0 if protein+fat exceed target"
        assert total_kcal > daily_target, "Total macros exceed daily_target!"
