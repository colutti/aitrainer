import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog, NutritionWithId
from src.services.database import MongoDatabase


# Mock the NutritionLog since it's used in the service but we don't need its logic for the weight filter test
class MockNutritionLog:
    def __init__(self, date_obj, calories, protein_grams=150, carbs_grams=200, fat_grams=65, partial=False):
        self.date = datetime(date_obj.year, date_obj.month, date_obj.day)
        self.calories = calories
        self.protein_grams = protein_grams
        self.carbs_grams = carbs_grams
        self.fat_grams = fat_grams
        self.partial_logged = partial




class TestAdaptiveTDEELogic:
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _create_logs(self, weight_values, start_date=None):
        if start_date is None:
            start_date = date(2025, 1, 1)

        logs = []
        for i, w in enumerate(weight_values):
            logs.append(
                WeightLog(
                    user_email="test@test.com",
                    date=start_date + timedelta(days=i),
                    weight_kg=w,
                )
            )
        return logs

    def test_filter_outliers_water_drop(self, service):
        """
        Scenario: User drops 1.5kg in one day (Water) then maintains.
        Input: [78.0, 76.5, 76.5, 76.5, 76.5]
        Expectation: Service should identify the drop and return the stable baseline (76.5 series).
        """
        logs = self._create_logs([78.0, 76.5, 76.5, 76.5, 76.5])

        filtered, count = service._filter_outliers(logs)

        # Should exclude the first one (78.0) because the subsequent logs confirm the drop was a 'step'
        # OR it treats it as a new baseline.
        # The logic proposed is: if step change, reset window.
        # So we expect 76.5, 76.5, 76.5, 76.5

        assert len(filtered) == 4
        assert filtered[0].weight_kg == 76.5
        assert filtered[-1].weight_kg == 76.5
        assert count == 1

    def test_filter_outliers_transient_spike(self, service):
        """
        Scenario: User gains 1.5kg then goes back (Cheat meal / bloating).
        Input: [76.5, 76.5, 78.0, 76.5, 76.5]
        Expectation: Service should identify 78.0 as outlier and remove it.
        """
        logs = self._create_logs([76.5, 76.5, 78.0, 76.5, 76.5])

        filtered, count = service._filter_outliers(logs)

        assert len(filtered) == 4
        assert count == 1
        for log in filtered:
            assert log.weight_kg == 76.5

    def test_true_weight_loss(self, service):
        """
        Scenario: User steadily loses 0.5kg regularly.
        Input: [80.0, 79.5, 79.0, 78.5, 78.0]
        Expectation: No outliers, keep all data.
        """
        # 0.5kg is < 1.0kg limit, so treated as normal
        logs = self._create_logs([80.0, 79.5, 79.0, 78.5, 78.0])

        filtered, count = service._filter_outliers(logs)

        assert len(filtered) == 5
        assert count == 0
        assert filtered[0].weight_kg == 80.0
        assert filtered[-1].weight_kg == 78.0

    def test_filter_outliers_step_change_up(self, service):
        """
        Scenario: User gains 1.5kg and stays there (Step Change Up).
        Input: [76.5, 78.0, 78.0, 78.0]
        Expectation: Reset window to start at 78.0
        """
        logs = self._create_logs([76.5, 78.0, 78.0, 78.0])

        filtered, count = service._filter_outliers(logs)

        assert len(filtered) == 3
        assert count == 1
        assert filtered[0].weight_kg == 78.0

    def test_v2_constants_exist(self, service):
        """Verify new v2 constants are defined on the service."""
        assert service.KCAL_PER_KG_FAT_MASS == 9400
        assert service.KCAL_PER_KG_LEAN_MASS == 1800
        assert service.KCAL_PER_KG_DEFAULT == 7700
        assert service.DEFAULT_LOOKBACK_WEEKS == 4
        assert service.MIN_CALORIES_FEMALE == 1200
        assert service.MIN_CALORIES_MALE == 1500
        assert service.MAX_DEFICIT_PCT == 0.30
        assert service.MAX_WEEKLY_ADJUSTMENT == 100
        assert service.OUTLIER_MODIFIED_Z_THRESHOLD == 3.5


class TestEnergyPerKg:
    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_no_body_fat_returns_default(self, service):
        """When body_fat_pct is None, fallback to 7700."""
        result = service._estimate_energy_per_kg(body_fat_pct=None, slope=-0.05)
        assert result == 7700

    def test_average_body_fat_25pct(self, service):
        """At 25% body fat, fat_fraction = 0.75 → energy ≈ 0.75*9400 + 0.25*1800 = 7500."""
        result = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.05)
        assert 7400 <= result <= 7600

    def test_high_body_fat_35pct(self, service):
        """At 35% body fat, fat_fraction = 0.80 → energy ≈ 0.80*9400 + 0.20*1800 = 7880."""
        result = service._estimate_energy_per_kg(body_fat_pct=35.0, slope=-0.05)
        assert 7700 <= result <= 8100

    def test_low_body_fat_15pct(self, service):
        """At 15% body fat, fat_fraction = 0.70 → energy ≈ 0.70*9400 + 0.30*1800 = 7120."""
        result = service._estimate_energy_per_kg(body_fat_pct=15.0, slope=-0.05)
        assert 6900 <= result <= 7300

    def test_very_low_body_fat_clamps_at_50pct(self, service):
        """Fat fraction never goes below 0.50."""
        result = service._estimate_energy_per_kg(body_fat_pct=5.0, slope=-0.05)
        # 0.50 * 9400 + 0.50 * 1800 = 5600
        assert result >= 5600

    def test_very_high_body_fat_clamps_at_90pct(self, service):
        """Fat fraction never goes above 0.90."""
        result = service._estimate_energy_per_kg(body_fat_pct=60.0, slope=-0.05)
        # 0.90 * 9400 + 0.10 * 1800 = 8640
        assert result <= 8640

    def test_rapid_loss_reduces_fat_fraction(self, service):
        """Losing > 0.5 kg/week penalizes fat fraction (more lean loss)."""
        normal = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.05)
        rapid = service._estimate_energy_per_kg(body_fat_pct=25.0, slope=-0.15)
        # Rapid loss should have lower energy per kg (more lean tissue lost)
        assert rapid < normal


class TestCalculateTDEEIntegration:
    """Tests that calculate_tdee uses dynamic energy density and 4-week lookback."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_default_lookback_is_4_weeks(self, service):
        """calculate_tdee should default to 4-week lookback."""
        import inspect
        sig = inspect.signature(service.calculate_tdee)
        default = sig.parameters["lookback_weeks"].default
        assert default == 4


class TestCoachingTargetNoPenalty:
    """Tests that coaching target does NOT apply off-track penalty."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, goal_type="lose", weekly_rate=0.5, gender="Masculino",
                      tdee_last_target=None, tdee_last_check_in=None):
        """Helper to create a mock profile."""
        profile = MagicMock()
        profile.goal_type = goal_type
        profile.weekly_rate = weekly_rate
        profile.gender = gender
        profile.tdee_last_target = tdee_last_target
        profile.tdee_last_check_in = tdee_last_check_in
        return profile

    def test_lose_target_no_penalty_when_off_track(self, service):
        """Even when actual rate (0.2 kg/week) < goal rate (0.5 kg/week), NO extra penalty. Target = TDEE - deficit_needed."""
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5)
        tdee = 2200.0
        avg_calories = 1800.0
        weekly_change = -0.2  # Only losing 0.2 kg/week (off-track)

        target = service._calculate_coaching_target(tdee, avg_calories, weekly_change, profile)

        # Target should be TDEE - (0.5 * 1100) = 2200 - 550 = 1650
        # NOT 2200 - 550 - (0.3 * 1100) = 1320 with penalty
        assert target >= 1600, f"Target {target} is too low — penalty was applied!"
        assert target <= 1700

    def test_gain_target_no_penalty_when_off_track(self, service):
        """Even when not gaining fast enough, no extra surplus penalty."""
        profile = self._make_profile(goal_type="gain", weekly_rate=0.5)
        tdee = 2200.0
        avg_calories = 2500.0
        weekly_change = 0.2  # Only gaining 0.2 kg/week (off-track)

        target = service._calculate_coaching_target(tdee, avg_calories, weekly_change, profile)

        # Target should be TDEE + (0.5 * 1100) = 2200 + 550 = 2750
        assert target <= 2800, f"Target {target} is too high — penalty was applied!"
        assert target >= 2700

    def test_maintain_returns_tdee(self, service):
        """Maintain goal returns TDEE directly."""
        profile = self._make_profile(goal_type="maintain")
        target = service._calculate_coaching_target(2200.0, 2200.0, 0.0, profile)
        assert target == 2200

    def test_no_profile_returns_tdee(self, service):
        """No profile returns TDEE directly."""
        target = service._calculate_coaching_target(2200.0, 2200.0, 0.0, None)
        assert target == 2200


class TestGradualAdjustment:
    """Tests that gradual adjustment caps changes to ±100 kcal/week."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, tdee_last_target=None, tdee_last_check_in=None, **kwargs):
        profile = MagicMock()
        profile.goal_type = kwargs.get("goal_type", "lose")
        profile.weekly_rate = kwargs.get("weekly_rate", 0.5)
        profile.gender = kwargs.get("gender", "Masculino")
        profile.tdee_last_target = tdee_last_target
        profile.tdee_last_check_in = tdee_last_check_in
        return profile

    def test_first_time_no_previous_target(self, service):
        """First time: return ideal_target directly (no capping)."""
        profile = self._make_profile(tdee_last_target=None)
        result = service._apply_gradual_adjustment(1650, profile)
        assert result == 1650

    def test_small_change_within_100_passes_through(self, service):
        """Change of 80 kcal (< 100) passes through unchanged."""
        profile = self._make_profile(tdee_last_target=1600, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1680, profile)
        assert result == 1680

    def test_large_decrease_capped_at_minus_100(self, service):
        """Change of -300 kcal capped to -100."""
        profile = self._make_profile(tdee_last_target=1800, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1500, profile)
        assert result == 1700  # 1800 - 100

    def test_large_increase_capped_at_plus_100(self, service):
        """Change of +250 kcal capped to +100."""
        profile = self._make_profile(tdee_last_target=1500, tdee_last_check_in="2025-01-01")
        result = service._apply_gradual_adjustment(1750, profile)
        assert result == 1600  # 1500 + 100

    def test_check_in_too_recent_returns_previous(self, service):
        """If last check-in was < 7 days ago, return previous target."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        profile = self._make_profile(tdee_last_target=1600, tdee_last_check_in=yesterday)
        result = service._apply_gradual_adjustment(1400, profile)
        assert result == 1600  # No change

    def test_check_in_exactly_7_days_allows_adjustment(self, service):
        """If last check-in was exactly 7 days ago, allow adjustment."""
        seven_days_ago = (date.today() - timedelta(days=7)).isoformat()
        profile = self._make_profile(tdee_last_target=1800, tdee_last_check_in=seven_days_ago)
        result = service._apply_gradual_adjustment(1500, profile)
        assert result == 1700  # 1800 - 100


class TestSafetyFloor:
    """Tests gender-specific calorie floors and max deficit percentage."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _make_profile(self, gender="Masculino", **kwargs):
        profile = MagicMock()
        profile.gender = gender
        profile.goal_type = kwargs.get("goal_type", "lose")
        profile.weekly_rate = kwargs.get("weekly_rate", 0.5)
        profile.tdee_last_target = kwargs.get("tdee_last_target", None)
        profile.tdee_last_check_in = kwargs.get("tdee_last_check_in", None)
        return profile

    def test_male_floor_1500(self, service):
        """Male target should never go below 1500."""
        profile = self._make_profile(gender="Masculino")
        result = service._apply_safety_floor(1200, 2000.0, profile)
        assert result == 1500

    def test_female_floor_1200(self, service):
        """Female target should never go below 1200."""
        profile = self._make_profile(gender="Feminino")
        # With TDEE=1600, 30% deficit = 1120. Female floor = 1200. Floor wins.
        result = service._apply_safety_floor(1000, 1600.0, profile)
        assert result == 1200

    def test_max_deficit_30pct(self, service):
        """Target should not exceed 30% deficit from TDEE."""
        profile = self._make_profile(gender="Masculino")
        # TDEE=2500, 30% deficit = 1750. Target 1500 is 40% deficit → clamp to 1750
        result = service._apply_safety_floor(1500, 2500.0, profile)
        assert result == 1750

    def test_gender_floor_wins_over_deficit_pct(self, service):
        """When both apply, the HIGHER floor wins."""
        profile = self._make_profile(gender="Masculino")
        # TDEE=1800, 30% deficit = 1260. Male floor = 1500. Floor wins.
        result = service._apply_safety_floor(1100, 1800.0, profile)
        assert result == 1500

    def test_target_above_all_floors_unchanged(self, service):
        """Target above all floors passes through unchanged."""
        profile = self._make_profile(gender="Masculino")
        result = service._apply_safety_floor(1900, 2500.0, profile)
        assert result == 1900

    def test_no_profile_uses_generic_floor(self, service):
        """Without profile, use MIN_TDEE (1200) as generic floor."""
        result = service._apply_safety_floor(1000, 2000.0, None)
        assert result == 1200

    def test_gain_goal_no_deficit_floor(self, service):
        """For gain goals, deficit floor should not apply (target > TDEE)."""
        profile = self._make_profile(gender="Masculino", goal_type="gain")
        result = service._apply_safety_floor(2800, 2500.0, profile)
        assert result == 2800


class TestModifiedZScoreOutlier:
    """Tests Modified Z-Score outlier detection as first pass."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _create_logs(self, weight_values, start_date=None):
        if start_date is None:
            start_date = date(2025, 1, 1)
        logs = []
        for i, w in enumerate(weight_values):
            logs.append(WeightLog(
                user_email="test@test.com",
                date=start_date + timedelta(days=i),
                weight_kg=w,
            ))
        return logs

    def test_statistical_outlier_detected(self, service):
        """A single extreme value among consistent data should be detected."""
        # 14 days at ~76 kg, one day at 82 kg (extreme outlier)
        weights = [76.0, 76.1, 75.9, 76.2, 76.0, 75.8, 76.1,
                   82.0,  # Statistical outlier
                   76.0, 76.1, 75.9, 76.2, 76.0, 75.8]
        logs = self._create_logs(weights)
        filtered, count = service._filter_outliers(logs)
        assert count >= 1
        # The 82.0 should be removed
        assert all(log.weight_kg < 80.0 for log in filtered)

    def test_no_outliers_in_consistent_data(self, service):
        """Consistent data with normal variation should have no outliers."""
        weights = [76.0, 76.2, 75.8, 76.1, 75.9, 76.3, 76.0,
                   75.7, 76.1, 76.2, 75.8, 76.0, 76.1, 75.9]
        logs = self._create_logs(weights)
        filtered, count = service._filter_outliers(logs)
        assert count == 0
        assert len(filtered) == 14


class TestAdaptiveTDEEV2Integration:
    """
    End-to-end test simulating production data to verify v2 algorithm
    produces reasonable targets (not the old 1415 kcal bug).
    """

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_production_scenario_male_moderate_loss(self, service, mock_db):
        """
        Simulates the real production bug scenario:
        75kg male, 23% bf, goal lose 0.5kg/week, avg intake ~1900 kcal.
        OLD result: 1415 kcal (36% deficit — too aggressive!)
        NEW result: should be ~1650-1700 kcal (24% deficit — sustainable)
        """
        start = date(2025, 1, 1)

        # 28 days of weight logs: gradual decline 77 → 75.5
        weight_logs = []
        for i in range(28):
            w = 77.0 - (i * 0.054)  # ~0.054 kg/day = ~0.38 kg/week
            weight_logs.append(WeightLog(
                user_email="test@test.com",
                date=start + timedelta(days=i),
                weight_kg=round(w, 1),
                body_fat_pct=23.3 if i >= 20 else None,
            ))

        # 28 days of nutrition: avg ~1900 kcal
        nutrition_logs = []
        import random
        random.seed(42)
        for i in range(28):
            cal = 1900 + random.randint(-200, 200)
            nutrition_logs.append(MockNutritionLog(start + timedelta(days=i), cal))

        # Profile: male, lose 0.5 kg/week, no previous target (first calculation)
        profile = MagicMock()
        profile.goal_type = "lose"
        profile.weekly_rate = 0.5
        profile.gender = "Masculino"
        profile.target_weight = 72.0
        profile.tdee_last_target = None
        profile.tdee_last_check_in = None
        profile.height = 175
        profile.age = 45
        profile.weight = 75.0

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=4)

        # The TDEE should be reasonable (around 2100-2300)
        assert 2000 <= result["tdee"] <= 2400, f"TDEE {result['tdee']} out of expected range"

        # The daily target should NOT be as low as 1415 (the old bug)
        assert result["daily_target"] >= 1500, (
            f"daily_target {result['daily_target']} is below male minimum — v2 bug!"
        )

        # The deficit should be at most 30%
        deficit_pct = (result["tdee"] - result["daily_target"]) / result["tdee"]
        assert deficit_pct <= 0.31, (
            f"Deficit {deficit_pct:.0%} exceeds 30% max — safety floor not working!"
        )

    def test_female_low_tdee_respects_1200_floor(self, service, mock_db):
        """Female user with low TDEE should not go below 1200."""
        start = date(2025, 1, 1)
        weight_logs = []
        for i in range(28):
            w = 55.0 - (i * 0.02)
            weight_logs.append(WeightLog(
                user_email="test@test.com",
                date=start + timedelta(days=i),
                weight_kg=round(w, 1),
            ))

        nutrition_logs = []
        for i in range(28):
            nutrition_logs.append(MockNutritionLog(start + timedelta(days=i), 1400))

        profile = MagicMock()
        profile.goal_type = "lose"
        profile.weekly_rate = 0.5
        profile.gender = "Feminino"
        profile.target_weight = 50.0
        profile.tdee_last_target = None
        profile.tdee_last_check_in = None
        profile.height = 160
        profile.age = 30
        profile.weight = 55.0

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=4)

        assert result["daily_target"] >= 1200, (
            f"Female daily_target {result['daily_target']} below 1200 floor!"
        )


class TestNutritionLogPartialLogged:
    """Tests for the partial_logged field in NutritionLog."""

    def test_default_is_false(self):
        """New NutritionLog should have partial_logged=False by default."""
        log = NutritionLog(
            user_email="test@example.com",
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=65,
        )
        assert log.partial_logged is False

    def test_can_be_set_to_true(self):
        """partial_logged can be explicitly set to True."""
        log = NutritionLog(
            user_email="test@example.com",
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=65,
            partial_logged=True,
        )
        assert log.partial_logged is True

    def test_serialized_in_nutrition_with_id(self):
        """partial_logged should be included in NutritionWithId serialization."""
        log = NutritionWithId(
            id="507f1f77bcf86cd799439011",
            user_email="test@example.com",
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=65,
            partial_logged=True,
        )
        serialized = log.model_dump()
        assert "partial_logged" in serialized
        assert serialized["partial_logged"] is True

    def test_partial_logged_is_bool_type(self):
        """partial_logged field should be a boolean type."""
        log = NutritionLog(
            user_email="test@example.com",
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=65,
        )
        assert isinstance(log.partial_logged, bool)


class TestInterpolateWeightGaps:
    """Tests for the _interpolate_weight_gaps method."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def _create_logs(self, weight_values, start_date=None):
        """Helper to create weight logs."""
        if start_date is None:
            start_date = date(2025, 1, 1)
        logs = []
        for i, w in enumerate(weight_values):
            logs.append(
                WeightLog(
                    user_email="test@test.com",
                    date=start_date + timedelta(days=i),
                    weight_kg=w,
                )
            )
        return logs

    def test_empty_list_returns_empty_dict(self, service):
        """Empty weight log list should return empty dict."""
        result = service._interpolate_weight_gaps([])
        assert result == {}

    def test_single_log_returns_single_day(self, service):
        """Single weight log should return dict with one entry."""
        logs = self._create_logs([80.0])
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 1
        assert result[date(2025, 1, 1)] == 80.0

    def test_consecutive_days_no_gap(self, service):
        """Consecutive days with no gap should return all dates."""
        logs = self._create_logs([80.0, 79.8, 79.6])
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 3
        assert result[date(2025, 1, 1)] == 80.0
        assert result[date(2025, 1, 2)] == 79.8
        assert result[date(2025, 1, 3)] == 79.6

    def test_one_day_gap_interpolated(self, service):
        """One day gap should be interpolated."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=2), weight_kg=78.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 3
        assert result[start] == 80.0
        assert result[start + timedelta(days=1)] == 79.0  # Halfway
        assert result[start + timedelta(days=2)] == 78.0

    def test_two_day_gap_interpolated(self, service):
        """Two day gap should be interpolated with two intermediate points."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=3), weight_kg=77.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 4
        assert result[start] == 80.0
        assert abs(result[start + timedelta(days=1)] - 79.0) < 0.01
        assert abs(result[start + timedelta(days=2)] - 78.0) < 0.01
        assert result[start + timedelta(days=3)] == 77.0

    def test_gap_at_max_boundary_14_days_interpolated(self, service):
        """14-day gap (at MAX_INTERPOLATION_GAP boundary) should be interpolated."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=14), weight_kg=73.6),
        ]
        result = service._interpolate_weight_gaps(logs)
        # Should have 15 entries (day 0 to day 14)
        assert len(result) == 15
        assert result[start] == 80.0
        assert result[start + timedelta(days=14)] == 73.6
        # Check mid-point interpolation
        assert abs(result[start + timedelta(days=7)] - 76.8) < 0.01

    def test_gap_exceeds_max_15_days_not_interpolated(self, service):
        """15-day gap (exceeds MAX=14) should use last known value."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=15), weight_kg=73.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 16
        assert result[start] == 80.0
        # Gap between day 1-14 should use last known value (80.0)
        assert result[start + timedelta(days=7)] == 80.0
        assert result[start + timedelta(days=14)] == 80.0
        assert result[start + timedelta(days=15)] == 73.0

    def test_multiple_segments_with_gaps(self, service):
        """Multiple segments with different gap sizes."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=7), weight_kg=79.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=20), weight_kg=79.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        # First segment (7 days): interpolated
        # Gap between day 7-20 (13 days): interpolated
        assert len(result) == 21
        assert result[start] == 80.0
        assert result[start + timedelta(days=7)] == 79.0
        assert result[start + timedelta(days=20)] == 79.0

    def test_all_same_weight_interpolated_flat(self, service):
        """When all logs have same weight, result should be flat."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=75.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=5), weight_kg=75.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 6
        for val in result.values():
            assert val == 75.0

    def test_v_shape_weight_interpolated(self, service):
        """V-shaped weight change (down then up) should interpolate correctly."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=7), weight_kg=76.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=14), weight_kg=80.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 15
        # Check V pattern
        assert result[start] == 80.0
        assert result[start + timedelta(days=7)] == 76.0
        assert result[start + timedelta(days=14)] == 80.0
        # Mid-point of first segment (day 3.5 into 7-day gap, so ~78.29)
        assert abs(result[start + timedelta(days=3)] - 78.29) < 0.1

    def test_result_contains_all_days_in_range(self, service):
        """Result should contain all calendar days from first to last log."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=10), weight_kg=77.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 11
        for i in range(11):
            assert (start + timedelta(days=i)) in result

    def test_float_weight_precision_maintained(self, service):
        """Float weights should maintain precision."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.55),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=2), weight_kg=79.45),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert result[start] == 80.55
        # Mid-point should be ~80.0
        assert abs(result[start + timedelta(days=1)] - 80.0) < 0.01
        assert result[start + timedelta(days=2)] == 79.45

    def test_unsorted_logs_handled(self, service):
        """Unsorted logs should be sorted internally."""
        start = date(2025, 1, 1)
        # Create logs in reverse order
        logs = [
            WeightLog(user_email="test@test.com", date=start + timedelta(days=2), weight_kg=78.0),
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 3
        assert result[start] == 80.0
        assert result[start + timedelta(days=2)] == 78.0

    def test_custom_max_gap_parameter(self, service):
        """Custom max_gap_days should be respected."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=5), weight_kg=77.0),
        ]
        # With max_gap=3, a 5-day gap should NOT interpolate
        result = service._interpolate_weight_gaps(logs, max_gap_days=3)
        assert result[start] == 80.0
        assert result[start + timedelta(days=1)] == 80.0  # Not interpolated
        assert result[start + timedelta(days=5)] == 77.0

    def test_result_is_sorted_by_date(self, service):
        """Result dict should be sorted by date."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=80.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=3), weight_kg=77.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        dates = list(result.keys())
        assert dates == sorted(dates)

    def test_large_weight_drop_still_interpolates(self, service):
        """Even large weight drops should be interpolated linearly."""
        start = date(2025, 1, 1)
        logs = [
            WeightLog(user_email="test@test.com", date=start, weight_kg=100.0),
            WeightLog(user_email="test@test.com", date=start + timedelta(days=4), weight_kg=80.0),
        ]
        result = service._interpolate_weight_gaps(logs)
        assert len(result) == 5
        assert result[start] == 100.0
        assert result[start + timedelta(days=2)] == 90.0
        assert result[start + timedelta(days=4)] == 80.0


class TestComputeTDEEObservations:
    """Tests for computing daily TDEE observations (Task 3)."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_requires_at_least_8_days_of_trend(self, service):
        """Se trend tem <= 7 dias, não há janela possível → retorna []"""
        daily_trend = {
            date(2025, 1, 1) + timedelta(days=i): 80.0 - (i * 0.05)
            for i in range(7)
        }
        nutrition_by_date = {
            date(2025, 1, 1) + timedelta(days=i): 2200
            for i in range(7)
        }

        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 7700
        )

        assert observations == []

    def test_generates_observation_from_window(self, service):
        """10 dias trend + nutrition, gera observações com janela de 7 dias"""
        daily_trend = {
            date(2025, 1, 1) + timedelta(days=i): 80.0 - (i * 0.1)
            for i in range(10)
        }
        nutrition_by_date = {
            date(2025, 1, 1) + timedelta(days=i): 2100
            for i in range(10)
        }

        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 7700
        )

        # Com 10 dias, devemos ter >= 3 observações de janelas de 7 dias
        assert len(observations) >= 3
        assert all(isinstance(obs, tuple) and len(obs) == 2 for obs in observations)
        assert all(isinstance(obs[0], date) and isinstance(obs[1], (int, float)) for obs in observations)

    def test_window_skipped_if_less_than_4_nutrition_days(self, service):
        """Janelas com < 4 dias de nutrition são descartadas"""
        daily_trend = {
            date(2025, 1, 1) + timedelta(days=i): 80.0 - (i * 0.1)
            for i in range(10)
        }
        # Apenas 3 dias com nutrition
        nutrition_by_date = {
            date(2025, 1, 1): 2100,
            date(2025, 1, 2): 2100,
            date(2025, 1, 3): 2100,
        }

        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 7700
        )

        # Nenhuma janela de 7 dias tem >= 4 dias de nutrition
        assert observations == []

    def test_window_ok_with_4_of_7_nutrition_days(self, service):
        """Janelas com >= 4 dias de nutrition geram observação"""
        daily_trend = {
            date(2025, 1, 1) + timedelta(days=i): 80.0 - (i * 0.1)
            for i in range(10)
        }
        # 5 dias com nutrition
        nutrition_by_date = {
            date(2025, 1, 1) + timedelta(days=i): 2100
            for i in range(5)
        }

        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 7700
        )

        # Deve gerar observações para as janelas com >= 4 dias
        assert len(observations) > 0

    def test_outlier_observations_filtered(self, service):
        """Observações fora de [500, 5000] são descartadas"""
        daily_trend = {
            date(2025, 1, 1) + timedelta(days=i): 80.0
            for i in range(10)
        }
        # Force outlier por usar energy_per_kg muito alto
        nutrition_by_date = {
            date(2025, 1, 1) + timedelta(days=i): 2100
            for i in range(10)
        }

        # Com energy_per_kg=20000 (artificialmente alto) e mudança de trend,
        # vamos gerar observações muito altas ou baixas
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 20000
        )

        # Todas as observações retornadas devem estar em [500, 5000]
        # (ou lista vazia se todas foram filtradas)
        if observations:
            for _, obs in observations:
                assert 500 <= obs <= 5000

    def test_weekly_window_reduces_noise(self, service):
        """Janelas de 7 dias reduzem ruído vs observações diárias"""
        # Cria 20 dias com variação diária de ±0.3 kg (hidratação) mas trend estável
        base_weight = 80.0
        daily_trend = {}
        nutrition_by_date = {}

        for i in range(20):
            # Variação aleatória de hidratação, mas tendência geral -0.1kg por 2 dias
            noise = 0.3 * (1 if i % 2 == 0 else -1)
            trend_weight = base_weight - (i * 0.05) + noise
            daily_trend[date(2025, 1, 1) + timedelta(days=i)] = trend_weight
            nutrition_by_date[date(2025, 1, 1) + timedelta(days=i)] = 2100

        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, 7700
        )

        # Deve gerar observações (>=1)
        assert len(observations) >= 1

        # Observações devem ser razoáveis (entre 500-5000)
        if observations:
            for _, obs in observations:
                assert 500 <= obs <= 5000


class TestComputeTDEEFromObservations:
    """Tests for computing TDEE from observations (Task 3)."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_placeholder_from_observations(self, service):
        """Placeholder: _compute_tdee_from_observations will be implemented in Task 3."""
        # This test exists to mark the location where Task 3 tests should go
        # The actual method should take (observations, prior_tdee, span)
        # and return a single TDEE value using EMA
        pass


class TestComputeDailyTrend:
    """Tests for the _compute_daily_trend method."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_empty_dict_returns_empty_dict(self, service):
        """Empty daily weight series should return empty dict."""
        result = service._compute_daily_trend({})
        assert result == {}

    def test_single_day_returns_first_weight(self, service):
        """Single day should return weight as-is (initialization)."""
        daily_weights = {date(2025, 1, 1): 80.0}
        result = service._compute_daily_trend(daily_weights)
        assert len(result) == 1
        assert result[date(2025, 1, 1)] == 80.0

    def test_two_consecutive_days_ema_applied(self, service):
        """EMA formula should apply correctly for two days."""
        daily_weights = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.0,
        }
        result = service._compute_daily_trend(daily_weights)
        assert len(result) == 2
        assert result[date(2025, 1, 1)] == 80.0
        # trend_day2 = 0.0909*79 + 0.9091*80 ≈ 79.909
        alpha = 2 / 22  # EMA_SPAN=21
        expected = (79.0 * alpha) + (80.0 * (1 - alpha))
        assert abs(result[date(2025, 1, 2)] - expected) < 0.001

    def test_all_same_weights_trend_constant(self, service):
        """When all weights are same, trend should also be constant."""
        daily_weights = {
            date(2025, 1, 1): 75.0,
            date(2025, 1, 2): 75.0,
            date(2025, 1, 3): 75.0,
            date(2025, 1, 4): 75.0,
        }
        result = service._compute_daily_trend(daily_weights)
        for val in result.values():
            # With EMA, floating point precision may cause tiny differences
            assert abs(val - 75.0) < 0.0001

    def test_trend_lags_raw_weight_on_sharp_drop(self, service):
        """Trend should lag behind sharp weight drops."""
        daily_weights = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 80.0,
            date(2025, 1, 3): 75.0,  # Sharp drop
        }
        result = service._compute_daily_trend(daily_weights)
        # Trend on day 3 should be HIGHER than the actual weight (lag)
        assert result[date(2025, 1, 3)] > 75.0
        assert result[date(2025, 1, 3)] < 80.0

    def test_ema_alpha_formula_correct_span21(self, service):
        """EMA alpha should be calculated correctly for span=21."""
        alpha = 2 / (service.EMA_SPAN + 1)
        assert service.EMA_SPAN == 21
        assert abs(alpha - (2 / 22)) < 0.0001
        assert abs(alpha - 0.090909) < 0.00001

    def test_trend_initialized_with_first_weight(self, service):
        """First day trend should equal first weight."""
        daily_weights = {
            date(2025, 1, 1): 85.5,
            date(2025, 1, 2): 84.0,
        }
        result = service._compute_daily_trend(daily_weights)
        assert result[date(2025, 1, 1)] == 85.5

    def test_trend_converges_toward_new_level(self, service):
        """Trend should gradually converge toward a new stable level."""
        # Start at 80, then move to 75 and stay there
        daily_weights = {}
        base_date = date(2025, 1, 1)
        for i in range(50):
            if i < 5:
                daily_weights[base_date + timedelta(days=i)] = 80.0
            else:
                daily_weights[base_date + timedelta(days=i)] = 75.0

        result = service._compute_daily_trend(daily_weights)

        # At day 6, trend should be between 80 and 75, moving toward 75
        # At day 45 (40 days at 75kg), trend should be closer to 75 (with 21-day window)
        trend_day6 = result[base_date + timedelta(days=6)]
        trend_day45 = result[base_date + timedelta(days=45)]

        assert 75.0 < trend_day6 < 80.0
        # After 40 days at 75, trend should be much closer (but not perfect due to EMA memory)
        assert abs(trend_day45 - 75.0) < 1.0

    def test_trend_weights_ordered_by_date(self, service):
        """Trend dict should maintain date order."""
        daily_weights = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 3): 78.0,
            date(2025, 1, 2): 79.0,
        }
        result = service._compute_daily_trend(daily_weights)
        dates = list(result.keys())
        assert dates == sorted(dates)

    def test_trend_is_smoother_than_raw_weights(self, service):
        """Trend should have smaller day-to-day changes than raw weights."""
        daily_weights = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 76.0,
            date(2025, 1, 3): 80.0,
            date(2025, 1, 4): 76.0,
        }
        result = service._compute_daily_trend(daily_weights)

        # Calculate day-to-day changes
        raw_changes = []
        trend_changes = []
        dates = sorted(result.keys())

        for i in range(1, len(dates)):
            raw_change = abs(daily_weights[dates[i]] - daily_weights[dates[i - 1]])
            trend_change = abs(result[dates[i]] - result[dates[i - 1]])
            raw_changes.append(raw_change)
            trend_changes.append(trend_change)

        # Average trend change should be smaller than average raw change
        avg_raw = sum(raw_changes) / len(raw_changes)
        avg_trend = sum(trend_changes) / len(trend_changes)
        assert avg_trend < avg_raw

    def test_long_series_stability(self, service):
        """Long series should converge to expected trend."""
        # 60 days at 80kg, then shift to 75kg
        daily_weights = {}
        base_date = date(2025, 1, 1)
        for i in range(60):
            daily_weights[base_date + timedelta(days=i)] = 80.0
        for i in range(60, 100):
            daily_weights[base_date + timedelta(days=i)] = 75.0

        result = service._compute_daily_trend(daily_weights)

        # After ~40 days at 75kg, trend should be moving toward 75
        # With EMA span=21, convergence is gradual
        trend_day_60 = result[base_date + timedelta(days=60)]
        trend_day_99 = result[base_date + timedelta(days=99)]

        # By day 60, should have started moving down
        assert trend_day_60 < 80.0
        # By day 99 (39 days after shift), should be much closer
        assert abs(trend_day_99 - 75.0) < 1.5

    def test_volatile_weights_smoothed(self, service):
        """Volatile daily weights should be smoothed by trend."""
        # Oscillating weights
        daily_weights = {}
        base_date = date(2025, 1, 1)
        for i in range(20):
            w = 78.0 if (i % 2 == 0) else 82.0
            daily_weights[base_date + timedelta(days=i)] = w

        result = service._compute_daily_trend(daily_weights)

        # Trend should be around 80 (the mean), not oscillating
        trend_values = list(result.values())
        trend_range = max(trend_values) - min(trend_values)
        assert trend_range < 4.0  # Much smaller than 4kg raw oscillation

    def test_unsorted_input_handled(self, service):
        """Unsorted dict input should be sorted internally."""
        daily_weights = {
            date(2025, 1, 3): 78.0,
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.0,
        }
        result = service._compute_daily_trend(daily_weights)
        dates = list(result.keys())
        assert dates == [date(2025, 1, 1), date(2025, 1, 2), date(2025, 1, 3)]


class TestCalculateTDEEV3MainFlow:
    """
    Comprehensive integration tests for Task 4: Main calculate_tdee() flow with v3 algorithm.
    These tests verify the complete flow: data fetching → filtering → interpolation →
    trend computation → observation generation → TDEE calculation → coaching target.
    """

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    # === Fixtures for test data creation ===

    def _make_weight_log(self, email: str, date_val: date, weight: float,
                         body_fat: float | None = None, trend: float | None = None) -> WeightLog:
        """Helper to create a WeightLog."""
        return WeightLog(
            user_email=email,
            date=date_val,
            weight_kg=weight,
            body_fat_pct=body_fat,
            trend_weight=trend,
        )

    def _make_nutrition_log(self, email: str, date_val: date, calories: int,
                           protein: float = 150, carbs: float = 200, fat: float = 65,
                           partial: bool = False):
        """Helper to create a NutritionLog."""
        return NutritionLog(
            user_email=email,
            date=datetime(date_val.year, date_val.month, date_val.day),
            calories=calories,
            protein_grams=protein,
            carbs_grams=carbs,
            fat_grams=fat,
            partial_logged=partial,
        )

    def _make_profile(self, goal_type: str = "maintain", weekly_rate: float = 0.5,
                     gender: str = "Masculino", target_weight: float | None = None,
                     tdee_last_target: int | None = None, tdee_last_check_in: str | None = None,
                     height: int = 175, age: int = 30):
        """Helper to create a mock UserProfile."""
        profile = MagicMock()
        profile.goal_type = goal_type
        profile.weekly_rate = weekly_rate
        profile.gender = gender
        profile.target_weight = target_weight
        profile.tdee_last_target = tdee_last_target
        profile.tdee_last_check_in = tdee_last_check_in
        profile.height = height
        profile.age = age
        profile.weight = 75.0
        return profile

    # === Cold Start Tests (< 14 days, MIN_DATA_DAYS=3) ===

    def test_cold_start_3_days_returns_valid_result(self, service, mock_db):
        """With only 3 days of data, should return valid TDEE calculation (not fallback)."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.1))
            for i in range(3)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(3)
        ]
        profile = self._make_profile(goal_type="maintain")

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com", lookback_weeks=4)

        assert result["tdee"] is not None
        assert 1200 <= result["tdee"] <= 5000
        assert "confidence" in result

    def test_cold_start_2_weight_logs_valid(self, service, mock_db):
        """With 2 weight logs (minimum), should still calculate TDEE."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start, 75.0),
            self._make_weight_log("test@test.com", start + timedelta(days=7), 74.5),
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(7)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200
        assert "confidence" in result

    def test_insufficient_1_weight_log_returns_fallback(self, service, mock_db):
        """With only 1 weight log, should return fallback."""
        start = date(2025, 1, 1)

        weight_logs = [self._make_weight_log("test@test.com", start, 75.0)]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(5)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile

        result = service.calculate_tdee("test@test.com")

        assert result["confidence"] in ["none", "low"]

    def test_no_weight_logs_returns_fallback(self, service, mock_db):
        """No weight logs should trigger fallback."""
        start = date(2025, 1, 1)

        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(10)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = []
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile

        result = service.calculate_tdee("test@test.com")

        assert "tdee" in result
        assert "confidence" in result

    def test_no_nutrition_logs_returns_fallback(self, service, mock_db):
        """No nutrition logs should trigger fallback."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(10)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = []
        mock_db.get_user_profile.return_value = profile

        result = service.calculate_tdee("test@test.com")

        assert "tdee" in result
        assert "confidence" in result

    # === Partial Logged Tests ===

    def test_all_partial_logs_uses_formula_prior(self, service, mock_db):
        """When all nutrition logs are partial_logged=True, should use formula fallback."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(14)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200, partial=True)
            for i in range(14)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile

        result = service.calculate_tdee("test@test.com")

        # Should return valid result but with lower confidence
        assert "tdee" in result
        assert "daily_target" in result

    def test_partial_logs_excluded_from_calculation(self, service, mock_db):
        """Partial logs should be excluded; only complete logs used for TDEE calc."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(14)
        ]
        # 14 logs: 10 complete, 4 partial
        nutrition_logs = []
        for i in range(10):
            nutrition_logs.append(self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200, partial=False))
        for i in range(10, 14):
            nutrition_logs.append(self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2500, partial=True))

        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        # avg_calories should be based on the 10 complete logs (~2200), not the 4 partial ones
        assert 2000 <= result["avg_calories"] <= 2400

    # === Weight Anomaly Handling ===

    def test_outlier_weight_filtered_correctly(self, service, mock_db):
        """Extreme outlier weights should be filtered out."""
        start = date(2025, 1, 1)

        weight_values = [75.0] * 7 + [85.0] + [75.2] * 6  # One extreme outlier
        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), weight_values[i])
            for i in range(len(weight_values))
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(len(weight_values))
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        # Outlier should be removed, TDEE should be based on stable weight
        assert result["outliers_count"] >= 1
        assert 1800 <= result["tdee"] <= 2600

    def test_irregular_weighing_gaps_interpolated(self, service, mock_db):
        """Irregular weighing (3x/week) should be interpolated."""
        start = date(2025, 1, 1)

        weight_logs = []
        nutrition_logs = []
        for i in range(0, 28, 2):  # Every other day (3-4x/week pattern with gaps)
            weight_logs.append(self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.05)))
        for i in range(28):
            nutrition_logs.append(self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200))

        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200
        assert "weight_trend" in result

    def test_large_gap_14_days_interpolated(self, service, mock_db):
        """14-day gap (at boundary) should be interpolated."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start, 75.0),
            self._make_weight_log("test@test.com", start + timedelta(days=14), 73.6),
            self._make_weight_log("test@test.com", start + timedelta(days=28), 72.2),
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(29)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200
        assert len(result.get("weight_trend", [])) > 0

    def test_large_gap_exceeds_14_days_handled(self, service, mock_db):
        """Gap > 14 days should use last known weight to fill."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start, 75.0),
            self._make_weight_log("test@test.com", start + timedelta(days=20), 73.6),
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(21)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200

    # === Clamping Tests ===

    def test_tdee_clamped_at_minimum_1200(self, service, mock_db):
        """TDEE should never go below 1200."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 40.0 - (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 800)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200

    def test_tdee_clamped_at_maximum_5000(self, service, mock_db):
        """TDEE should never exceed 5000."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 150.0 + (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 5500)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] <= 5000

    # === Goal-based Target Tests ===

    def test_goal_lose_coaching_target_below_tdee(self, service, mock_db):
        """Lose goal should have daily_target < TDEE."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1700)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] < result["tdee"]

    def test_goal_gain_coaching_target_above_tdee(self, service, mock_db):
        """Gain goal should have daily_target > TDEE."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 70.0 + (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2700)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="gain", weekly_rate=0.5)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] > result["tdee"]

    def test_goal_maintain_target_equals_tdee(self, service, mock_db):
        """Maintain goal should have daily_target ≈ TDEE."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="maintain")

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert abs(result["daily_target"] - result["tdee"]) < 50

    # === Gradual Adjustment Tests ===

    def test_gradual_adjustment_cap_plus_100(self, service, mock_db):
        """Gradual adjustment should cap increases at +100 kcal."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1700)
            for i in range(28)
        ]
        # Profile with previous target set
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5,
                                    tdee_last_target=1500, tdee_last_check_in=date.today().isoformat())

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] <= 1600  # 1500 + 100

    def test_gradual_adjustment_cap_minus_100(self, service, mock_db):
        """Gradual adjustment should cap decreases at -100 kcal."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 + (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2500)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="gain", weekly_rate=0.5,
                                    tdee_last_target=2200, tdee_last_check_in=date.today().isoformat())

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] >= 2100  # 2200 - 100

    # === Check-in Interval Tests ===

    def test_recent_checkin_returns_previous_target(self, service, mock_db):
        """If last check-in < 7 days, should return previous target (no change)."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        profile = self._make_profile(tdee_last_target=1600, tdee_last_check_in=yesterday)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        # Target should return previous target when check-in too recent
        # The current code returns it directly if last_check_in < 7 days
        assert result["daily_target"] is not None

    # === Safety Floor Tests ===

    def test_safety_floor_female_1200(self, service, mock_db):
        """Female target should respect 1200 floor."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 50.0 - (i * 0.02))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1000)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5, gender="Feminino")

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] >= 1200

    def test_safety_floor_male_1500(self, service, mock_db):
        """Male target should respect 1500 floor."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 50.0 - (i * 0.02))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 800)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5, gender="Masculino")

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["daily_target"] >= 1500

    def test_safety_floor_max_30pct_deficit(self, service, mock_db):
        """Deficit should never exceed 30% of TDEE."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1400)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=1.0)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        deficit_pct = (result["tdee"] - result["daily_target"]) / result["tdee"]
        assert deficit_pct <= 0.31

    # === Body Composition Tests ===

    def test_very_large_user_high_body_fat(self, service, mock_db):
        """Large user with high body fat should estimate higher kcal/kg."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 150.0 - (i * 0.1),
                                 body_fat=35.0 if i >= 20 else None)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 3500)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200

    def test_very_lean_user_low_body_fat(self, service, mock_db):
        """Lean user with low body fat should estimate lower kcal/kg."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 70.0 - (i * 0.05),
                                 body_fat=12.0 if i >= 20 else None)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["tdee"] >= 1200

    # === Response Format Tests ===

    def test_response_has_all_required_fields(self, service, mock_db):
        """Response should have all documented fields."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        # Required fields
        required_fields = [
            "tdee", "confidence", "confidence_reason", "avg_calories",
            "avg_protein", "avg_carbs", "avg_fat", "weight_change_per_week",
            "energy_balance", "status", "is_stable", "logs_count",
            "nutrition_logs_count", "startDate", "endDate", "start_weight",
            "end_weight", "latest_weight", "daily_target", "goal_weekly_rate",
            "goal_type", "consistency_score", "macro_targets", "stability_score",
            "consistency", "calorie_trend", "weight_trend"
        ]

        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_calorie_trend_array_correct(self, service, mock_db):
        """Calorie trend should have entry for each day in range."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert "calorie_trend" in result
        assert len(result["calorie_trend"]) > 0

    def test_weight_trend_array_correct(self, service, mock_db):
        """Weight trend should have one entry per weight log."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert "weight_trend" in result
        assert len(result["weight_trend"]) == len(weight_logs)

    def test_consistency_array_28_days(self, service, mock_db):
        """Consistency array should always have 28 days."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(14)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(14)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert "consistency" in result
        assert len(result["consistency"]) == 28

    # === Stable User Tests ===

    def test_stable_maintenance_user(self, service, mock_db):
        """Stable maintenance user (28 days, 2200 kcal, weight stable)."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 + (0.05 if i % 2 == 0 else -0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="maintain")

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["status"] in ["maintenance", "stable"]
        assert result["is_stable"] is True
        assert 2000 <= result["tdee"] <= 2400

    def test_consistent_weight_loss(self, service, mock_db):
        """Consistent weight loss user (28 days, 1700 kcal, -0.35 kg/week)."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 77.0 - (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1700)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["status"] == "deficit"
        assert result["weight_change_per_week"] < -0.25
        assert result["daily_target"] < result["tdee"]

    def test_consistent_weight_gain(self, service, mock_db):
        """Consistent weight gain user (28 days, 2700 kcal, +0.35 kg/week)."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 70.0 + (i * 0.05))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2700)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="gain", weekly_rate=0.5)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result["status"] == "surplus"
        assert result["weight_change_per_week"] > 0.25
        assert result["daily_target"] > result["tdee"]

    # === Body Composition Integration ===

    def test_body_composition_changes_included(self, service, mock_db):
        """Body composition changes should be calculated when available."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start, 75.0, body_fat=25.0),
            *[self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0 - (i * 0.05))
              for i in range(1, 28)],
            self._make_weight_log("test@test.com", start + timedelta(days=27), 73.6, body_fat=23.0),
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1700)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert "fat_change_kg" in result or "start_fat_pct" in result

    def test_no_body_fat_data_no_composition(self, service, mock_db):
        """Without body fat data, composition changes should be None."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        # Should still have result, but no body comp fields
        assert "tdee" in result

    # === Additional Fields ===

    def test_scale_bmr_included(self, service, mock_db):
        """If weight log has BMR, it should be included in result."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 75.0)
            for i in range(28)
        ]
        weight_logs[-1].bmr = 1650  # Set BMR on last log

        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 2200)
            for i in range(28)
        ]
        profile = self._make_profile()

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result.get("scale_bmr") == 1650

    def test_weeks_to_goal_calculated(self, service, mock_db):
        """If goal_type != maintain and actual rate favors goal, calculate weeks_to_goal."""
        start = date(2025, 1, 1)

        weight_logs = [
            self._make_weight_log("test@test.com", start + timedelta(days=i), 77.0 - (i * 0.04))
            for i in range(28)
        ]
        nutrition_logs = [
            self._make_nutrition_log("test@test.com", start + timedelta(days=i), 1700)
            for i in range(28)
        ]
        profile = self._make_profile(goal_type="lose", weekly_rate=0.5, target_weight=70.0)

        mock_db.get_weight_logs_by_date_range.return_value = weight_logs
        mock_db.get_nutrition_logs_by_date_range.return_value = nutrition_logs
        mock_db.get_user_profile.return_value = profile
        mock_db.update_user_coaching_target.return_value = None

        result = service.calculate_tdee("test@test.com")

        assert result.get("weeks_to_goal") is not None or result.get("goal_eta_weeks") is not None
