import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog


@pytest.fixture
def mock_db():
    db = MagicMock()
    # Default to None to avoid tests returning MagicMocks for profile by default
    db.get_user_profile.return_value = None
    return db


@pytest.fixture
def service(mock_db):
    return AdaptiveTDEEService(mock_db)


def test_tdee_insufficient_data(service, mock_db):
    mock_db.get_weight_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs_by_date_range.return_value = []

    result = service.calculate_tdee("test@test.com")

    assert result["tdee"] == 2079
    assert result["confidence"] == "none"


def test_tdee_calculation_maintenance(service, mock_db):
    # User maintains weight with constant calories
    today = date.today()
    start_date = today - timedelta(days=20)

    # 21 days of data
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=70.0,
        )
        for i in range(21)
    ]
    # 21 days of nutrition at 2500 kcal
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

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    # Weight change = 0, TDEE computed from v3 algorithm (observations + EMA)
    assert result["tdee"] == 2437  # v3 algo with EMA smoothing
    assert result["avg_calories"] == 2500
    assert result["weight_change_per_week"] == 0.0
    assert result["confidence"] == "high"  # High adherence


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
        weights.append(
            WeightLog(
                user_email="test@test.com",
                date=start_date + timedelta(days=i),
                weight_kg=w,
            )
        )

    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(days)
    ]

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

    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=70.0,
        )
        for i in range(21)
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date,
            calories=2500,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
    ]  # Just 1 log

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com")

    assert result["tdee"] == 2079  # Fallback estimate
    assert result["confidence"] == "low"  # v3: can return low-confidence result with insufficient nutrition


def test_get_current_targets(service, mock_db):
    # Mock TDEE calculation with daily_target from coaching logic
    service.calculate_tdee = MagicMock(
        return_value={"tdee": 2500, "daily_target": 1950, "confidence": "high"}
    )

    # Mock Profile
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.5
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"
    mock_db.get_user_profile.return_value = profile_mock

    targets = service.get_current_targets("test@test.com")

    # Target comes from calculate_tdee (which uses coaching logic)
    assert targets["tdee"] == 2500
    assert targets["daily_target"] == 1950
    assert "coaching" in targets["reason"]


def test_get_current_targets_gain(service, mock_db):
    # Mock TDEE calculation with daily_target from coaching logic
    service.calculate_tdee = MagicMock(
        return_value={"tdee": 2500, "daily_target": 2720, "confidence": "high"}
    )

    # Mock Profile
    profile_mock = MagicMock()
    profile_mock.goal_type = "gain"
    profile_mock.weekly_rate = 0.2
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_user_profile.return_value = profile_mock

    targets = service.get_current_targets("test@test.com")

    # Target comes from calculate_tdee (which uses coaching logic)
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
    weights.append(
        WeightLog(
            user_email="comp@test.com",
            date=start_date,
            weight_kg=80.0,
            body_fat_pct=25.0,
        )
    )
    # Create filler logs (composition not strictly needed for fillers in current logic unless we checked every log)
    # The new logic only checks first and last valid logs.
    for i in range(1, 20):
        weights.append(
            WeightLog(
                user_email="comp@test.com",
                date=start_date + timedelta(days=i),
                weight_kg=80.0 - (2.0 * i / 20),
            )
        )
    # Create end log
    weights.append(
        WeightLog(
            user_email="comp@test.com", date=today, weight_kg=78.0, body_fat_pct=23.0
        )
    )

    # Nutrition logs (needed to pass MIN_DATA_DAYS check)
    nutrition = [
        NutritionLog(
            user_email="comp@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(21)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("comp@test.com", lookback_weeks=3)

    assert "fat_change_kg" in result
    assert result["fat_change_kg"] == -2.06
    assert (
        result["muscle_change_kg"] == 0.06
    )  # Fallback calculation (no muscle_mass_pct)
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
        if i == 10:  # Spike!
            weight = 75.0
        weights.append(
            WeightLog(
                user_email="test@test.com",
                date=start_date + timedelta(days=i),
                weight_kg=weight,
            )
        )

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

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    assert result["outliers_count"] == 1
    assert result["weight_logs_count"] == 20  # 21 total - 1 outlier
    assert result["tdee"] == 2437  # v3 algo, outlier filtered correctly


def test_tdee_sparse_weight_logs(service, mock_db):
    """Verify separate counts for weight and nutrition logs."""
    today = date.today()
    start_date = today - timedelta(days=20)

    # 21 days of nutrition logs (Dense)
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

    # Only 3 weight logs (Sparse)
    weights = [
        WeightLog(user_email="test@test.com", date=start_date, weight_kg=70.0),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=10),
            weight_kg=70.0,
        ),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=20),
            weight_kg=70.0,
        ),
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
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=70.0,
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

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    assert result["confidence"] == "high"
    assert "Excelente" in result["confidence_reason"]

    # Poor nutrition data (just enough to calculate, but bad adherence)
    # 8 logs out of 21 days = ~38% adherence (< 60%)
    nutrition_poor = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2500,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(8)
    ]
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_poor

    result_poor = service.calculate_tdee("test@test.com", lookback_weeks=3)

    assert result_poor["confidence"] == "low"
    assert "Muitos gaps nos registros" in result_poor["confidence_reason"]


def test_tdee_eta_projection(service, mock_db):
    """Verify ETA projection for weight goal."""
    today = date.today()
    start_date = today - timedelta(days=20)

    # User loses 1kg in 20 days (0.35kg/week trend)
    # 81.0 -> 80.0
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=81.0 - (1.0 * i / 20),
        )
        for i in range(21)
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=100,
            carbs_grams=100,
            fat_grams=50,
        )
        for i in range(21)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    # Profile: Target 75kg, Goal Lose 0.5kg/week
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.target_weight = 75.0
    profile_mock.weekly_rate = 0.5
    profile_mock.height = 175  # Set required fields
    profile_mock.age = 30
    profile_mock.gender = "Masculino"
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    # Latest weight = 80.0. To go = 5kg.
    # Real trend = -0.35kg/week
    # ETA = 5 / 0.35 = ~14.3 weeks
    assert result["target_weight"] == 75.0
    assert result["weeks_to_goal"] is not None
    assert 13 < result["weeks_to_goal"] < 16

    # Goal ETA = 5 / 0.5 = 10 weeks
    assert result["goal_eta_weeks"] == 10.0


# Bug Fix Tests - Body Composition Calculation Issues


def test_latest_weight_is_actual_last_record(service, mock_db):
    """Bug Fix #1: Verifies that latest_weight is always the actual last weight in the database,
    not affected by outlier filtering."""
    today = date.today()
    start_date = today - timedelta(days=20)

    # Weights with an outlier that will trigger step change filtering
    weights = [
        WeightLog(user_email="test@test.com", date=start_date, weight_kg=77.7),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=7),
            weight_kg=78.3,
        ),  # outlier
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=8),
            weight_kg=76.8,
        ),  # step change
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=18),
            weight_kg=76.85,
        ),  # actual last
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=100,
            carbs_grams=100,
            fat_grams=50,
        )
        for i in range(21)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    # latest_weight should be 76.85 (actual last), not 77.7 (from filtered window)
    assert result["latest_weight"] == 76.85


def test_muscle_change_uses_real_muscle_mass_pct(service, mock_db):
    """Bug Fix #2: Verifies that muscle_change uses the actual muscle_mass_pct from the scale,
    not a derived value from (total_weight - fat)."""
    today = date.today()
    start_date = today - timedelta(days=13)

    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date,
            weight_kg=76.80,
            body_fat_pct=24.73,
            muscle_mass_pct=54.87,
        ),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=13),
            weight_kg=76.85,
            body_fat_pct=24.24,
            muscle_mass_pct=55.22,
        ),
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=100,
            carbs_grams=100,
            fat_grams=50,
        )
        for i in range(14)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    # Expected muscle change: (76.85 × 55.22%) - (76.80 × 54.87%) = 42.44 - 42.14 = +0.30 kg
    expected_muscle_change = (76.85 * 0.5522) - (76.80 * 0.5487)
    assert "muscle_change_kg" in result
    assert abs(result["muscle_change_kg"] - expected_muscle_change) < 0.1


def test_composition_uses_real_weights_not_regression(service, mock_db):
    """Bug Fix #2: Verifies that body composition uses actual weights from logs,
    not regression-predicted values."""
    today = date.today()
    start_date = today - timedelta(days=13)

    # Weights that are stable (no regression slope effect)
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date,
            weight_kg=76.8,
            body_fat_pct=24.73,
        ),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=6),
            weight_kg=76.8,
            body_fat_pct=24.50,
        ),
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=13),
            weight_kg=76.85,
            body_fat_pct=24.24,
        ),
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=2000,
            protein_grams=100,
            carbs_grams=100,
            fat_grams=50,
        )
        for i in range(14)
    ]

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    # Fat change should use REAL weights: (76.85 × 24.24%) - (76.8 × 24.73%)
    # Not regression weights which could be different
    expected_fat_change = (76.85 * 0.2424) - (76.8 * 0.2473)  # ≈ -0.36 kg
    assert abs(result["fat_change_kg"] - expected_fat_change) < 0.1


def test_tdee_returns_calorie_trend(service, mock_db):
    """Verify calorie_trend is returned in the response."""
    today = date.today()
    start_date = today - timedelta(days=20)
    
    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=70.0,
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

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition

    result = service.calculate_tdee("test@test.com", lookback_weeks=3)

    assert "calorie_trend" in result
    assert len(result["calorie_trend"]) == 21
    assert result["calorie_trend"][0]["calories"] == 2500
    assert result["calorie_trend"][0]["date"] == start_date.isoformat()


# ============================================================================
# Coaching Check-in Tests
# ============================================================================


def test_coaching_target_first_execution(service, mock_db):
    """First execution: should return ideal_target directly."""
    today = date.today()
    start_date = today - timedelta(days=20)

    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=80.0 - (0.23 * 7 * i / 20),  # Losing 0.23 kg/week
        )
        for i in range(21)
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=1900,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=50,
        )
        for i in range(21)
    ]

    # Profile with no previous target (first execution)
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.3
    profile_mock.tdee_last_target = None
    profile_mock.tdee_last_check_in = None
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # NEW LOGIC: ideal = TDEE - (goal_rate * 1100)
    # v3 EMA-based TDEE calculation with dynamic adjustments
    # Verify target is in reasonable range (allow ±50 tolerance)
    assert 1950 < result["daily_target"] < 2350, (
        f"Expected ideal_target in range 1950-2350, got {result['daily_target']}. "
        f"TDEE: {result['tdee']}, avg_calories: {result['avg_calories']}"
    )


def test_coaching_target_on_track(service, mock_db):
    """Check-in > 7 days: gradual adjustment applies, capping to ±100 from previous."""
    today = date.today()
    start_date = today - timedelta(days=20)

    weights = [
        WeightLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            weight_kg=80.0 - (0.23 * 7 * i / 20),  # Losing 0.23 kg/week
        )
        for i in range(21)
    ]
    nutrition = [
        NutritionLog(
            user_email="test@test.com",
            date=start_date + timedelta(days=i),
            calories=1900,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=50,
        )
        for i in range(21)
    ]

    # Profile with previous target = 1900, last check-in 8 days ago (past 7-day interval)
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.3
    profile_mock.tdee_last_target = 1900
    profile_mock.tdee_last_check_in = (today - timedelta(days=8)).isoformat()
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # Check-in > 7 days, so gradual adjustment applies:
    # Verify target is adjusting gradually (within ±10 of expected cap)
    assert 1990 <= result["daily_target"] <= 2010, (
        f"Expected daily_target ~2000 with gradual adjustment, got {result['daily_target']}"
    )




def test_coaching_target_check_in_within_7_days(service, mock_db):
    """Check-in < 7 days: return previous target unchanged."""
    today = date.today()
    start_date = today - timedelta(days=20)

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
            calories=1900,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=50,
        )
        for i in range(21)
    ]

    # Last check-in was 3 days ago
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.3
    profile_mock.tdee_last_target = 1850
    profile_mock.tdee_last_check_in = (today - timedelta(days=3)).isoformat()
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # Check-in < 7 days -> return prev_target unchanged
    assert result["daily_target"] == 1850


def test_coaching_target_offtrack_reduces_target(service, mock_db):
    """Check-in >= 7 days, off track: target should be below previous target."""
    today = date.today()
    start_date = today - timedelta(days=20)

    # Maintaining weight at high calories
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
            calories=2200,
            protein_grams=150,
            carbs_grams=250,
            fat_grams=80,
        )
        for i in range(21)
    ]

    # Previous target was 1950, user is off track (maintaining weight instead of losing)
    # Off-track penalty: ideal = TDEE - deficit_needed - gap_penalty ≈ 2200 - 330 - 330 = 1540
    # Result should be below prev_target=1950
    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.3
    profile_mock.tdee_last_target = 1950
    profile_mock.tdee_last_check_in = (today - timedelta(days=8)).isoformat()
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # Off track (maintaining, not losing) -> target should be below previous
    assert result["daily_target"] <= 1950  # Should be reduced vs prev_target


def test_coaching_target_goal_maintain(service, mock_db):
    """Goal maintain: return TDEE without coaching logic."""
    today = date.today()
    start_date = today - timedelta(days=20)

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

    profile_mock = MagicMock()
    profile_mock.goal_type = "maintain"
    profile_mock.weekly_rate = 0.0
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # Maintain -> return TDEE directly (should be ~2500)
    assert result["daily_target"] == result["tdee"]




def test_coaching_target_floor_1000_kcal(service, mock_db):
    """Never recommend below 1000 kcal floor."""
    today = date.today()
    start_date = today - timedelta(days=20)

    # Maintain weight at only 1500 kcal (impossible but test the floor)
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
            calories=1500,
            protein_grams=100,
            carbs_grams=150,
            fat_grams=40,
        )
        for i in range(21)
    ]

    profile_mock = MagicMock()
    profile_mock.goal_type = "lose"
    profile_mock.weekly_rate = 0.5
    profile_mock.tdee_last_target = None
    profile_mock.tdee_last_check_in = None
    profile_mock.height = 175  # Required for BMR calculation
    profile_mock.age = 30
    profile_mock.gender = "Masculino"

    mock_db.get_weight_logs_by_date_range.return_value = weights
    mock_db.get_nutrition_logs_by_date_range.return_value = nutrition
    mock_db.get_user_profile.return_value = profile_mock

    result = service.calculate_tdee("test@test.com")

    # Maintaining at 1500, goal 0.5/week
    # ideal = 1500 - (0.5 * 1100) = 1500 - 550 = 950
    # Floor: max(1000, 950) = 1000
    assert result["daily_target"] >= 1000
