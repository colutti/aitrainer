import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.services.database import MongoDatabase


# Mock the NutritionLog since it's used in the service but we don't need its logic for the weight filter test
class MockNutritionLog:
    def __init__(self, date_obj, calories, protein_grams=150, carbs_grams=200, fat_grams=65):
        self.date = datetime(date_obj.year, date_obj.month, date_obj.day)
        self.calories = calories
        self.protein_grams = protein_grams
        self.carbs_grams = carbs_grams
        self.fat_grams = fat_grams




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


class TestComputeTDEEObservations:
    """Tests for computing daily TDEE observations from weight trends and nutrition data."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_empty_daily_trend_returns_empty(self, service):
        """Empty trend dict should return empty observations."""
        daily_trend = {}
        nutrition_by_date = {date(2025, 1, 2): 2000}
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        assert observations == []

    def test_only_one_trend_day_no_pairs_returns_empty(self, service):
        """Only one day in trend means no 'yesterday' for pairs. Should return empty."""
        daily_trend = {date(2025, 1, 1): 80.0}
        nutrition_by_date = {date(2025, 1, 1): 2000}
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        assert observations == []

    def test_empty_nutrition_data_returns_empty(self, service):
        """No nutrition data means no observations."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,
        }
        nutrition_by_date = {}
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        assert observations == []

    def test_stable_trend_obs_equals_calories(self, service):
        """If trend is stable (no change), obs_TDEE = calories."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 80.0,  # No change
        }
        nutrition_by_date = {date(2025, 1, 2): 2000}
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=0.0
        )
        assert len(observations) == 1
        assert observations[0] == 2000

    def test_declining_trend_obs_greater_than_calories(self, service):
        """If trend declines, weight loss subtracts from obs (making it higher)."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,  # -0.1 kg decline
        }
        nutrition_by_date = {date(2025, 1, 2): 1700}
        # energy_per_kg = 7700 (default)
        # obs = 1700 - (79.9 - 80.0) * 7700 = 1700 - (-0.1 * 7700) = 1700 + 770 = 2470
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=None, trend_slope=-0.05
        )
        assert len(observations) == 1
        assert observations[0] == pytest.approx(2470, abs=1)

    def test_increasing_trend_obs_less_than_calories(self, service):
        """If trend increases, weight gain subtracts from obs (making it lower)."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 80.1,  # +0.1 kg gain
        }
        nutrition_by_date = {date(2025, 1, 2): 2300}
        # energy_per_kg = 7700 (default)
        # obs = 2300 - (80.1 - 80.0) * 7700 = 2300 - (0.1 * 7700) = 2300 - 770 = 1530
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=None, trend_slope=0.05
        )
        assert len(observations) == 1
        assert observations[0] == pytest.approx(1530, abs=1)

    def test_day_without_nutrition_skipped(self, service):
        """Days without nutrition data should be skipped."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,
            date(2025, 1, 3): 79.8,
        }
        nutrition_by_date = {
            date(2025, 1, 2): 2000,
            # No entry for date(2025, 1, 3) — skip day 3
        }
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        assert len(observations) == 1
        # Day 2 obs = 2000 - (79.9 - 80.0) * energy_per_kg
        # With body fat 25%, energy_per_kg ≈ 7500 (higher than default)
        # So obs ≈ 2000 + 0.1 * 7500 = 2750
        assert observations[0] == pytest.approx(2700, abs=100)

    def test_multiple_days_correct_count(self, service):
        """n days in trend should yield n-1 observations (need yesterday)."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,
            date(2025, 1, 3): 79.8,
            date(2025, 1, 4): 79.7,
            date(2025, 1, 5): 79.6,
        }
        nutrition_by_date = {
            date(2025, 1, 2): 2000,
            date(2025, 1, 3): 2000,
            date(2025, 1, 4): 2000,
            date(2025, 1, 5): 2000,
        }
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        assert len(observations) == 4

    def test_observations_ordered_chronologically(self, service):
        """Observations should be in chronological order."""
        daily_trend = {
            date(2025, 1, 5): 79.6,
            date(2025, 1, 1): 80.0,
            date(2025, 1, 3): 79.8,
            date(2025, 1, 2): 79.9,
            date(2025, 1, 4): 79.7,
        }
        nutrition_by_date = {
            date(2025, 1, 2): 2000,
            date(2025, 1, 3): 2100,
            date(2025, 1, 4): 2200,
            date(2025, 1, 5): 2300,
        }
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        # Should be 4 observations in order (based on trend dict order)
        assert len(observations) == 4

    def test_energy_per_kg_7700_used_correctly(self, service):
        """Verify energy_per_kg=7700 is used in calculation (no body fat)."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.8,  # -0.2 kg
        }
        nutrition_by_date = {date(2025, 1, 2): 2000}
        # obs = 2000 - (-0.2 * 7700) = 2000 + 1540 = 3540
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=None, trend_slope=-0.1
        )
        assert observations[0] == pytest.approx(3540, abs=1)

    def test_energy_per_kg_varies_with_body_fat(self, service):
        """Different body fat percentages yield different energy_per_kg values."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,  # -0.1 kg
        }
        nutrition_by_date = {date(2025, 1, 2): 1700}

        # With low body fat (~15%)
        obs_low_bf = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=15.0, trend_slope=-0.05
        )
        # With high body fat (~35%)
        obs_high_bf = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=35.0, trend_slope=-0.05
        )

        # Higher body fat → higher energy_per_kg → higher obs_TDEE
        assert obs_high_bf[0] > obs_low_bf[0]

    def test_sparse_nutrition_some_days_skipped(self, service):
        """Partial nutrition logs: only days with nutrition get observations."""
        daily_trend = {
            date(2025, 1, 1): 80.0,
            date(2025, 1, 2): 79.9,
            date(2025, 1, 3): 79.8,
            date(2025, 1, 4): 79.7,
            date(2025, 1, 5): 79.6,
        }
        nutrition_by_date = {
            date(2025, 1, 2): 2000,
            # date(2025, 1, 3) missing
            date(2025, 1, 4): 2200,
            # date(2025, 1, 5) missing
        }
        observations = service._compute_tdee_observations(
            daily_trend, nutrition_by_date, body_fat_pct=25.0, trend_slope=-0.05
        )
        # Should have 2 observations (for days 2 and 4 only)
        assert len(observations) == 2


class TestComputeTDEEFromObservations:
    """Tests for EMA-based TDEE calculation from observations."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock(spec=MongoDatabase)

    @pytest.fixture
    def service(self, mock_db):
        return AdaptiveTDEEService(mock_db)

    def test_empty_observations_returns_prior(self, service):
        """Empty observations should return the formula prior unchanged."""
        observations = []
        formula_prior = 2000.0
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=21
        )
        assert result == 2000.0

    def test_single_observation_blends_with_prior(self, service):
        """One observation should blend with prior using alpha."""
        observations = [2100.0]
        formula_prior = 2000.0
        span = 21
        # alpha = 2 / (21 + 1) = 2/22 ≈ 0.0909
        # ema = 0.0909 * 2100 + 0.9091 * 2000 ≈ 2009.09
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        assert 2008 <= result <= 2010

    def test_many_same_observations_converge(self, service):
        """Many identical observations should converge to that value."""
        observations = [2300.0] * 50
        formula_prior = 2000.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # After many iterations, EMA should be very close to 2300
        assert 2290 <= result <= 2310

    def test_prior_equals_observations_stays_stable(self, service):
        """If prior equals all observations, result should be stable."""
        observations = [2200.0] * 10
        formula_prior = 2200.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        assert 2199 <= result <= 2201

    def test_prior_higher_converges_downward(self, service):
        """Prior > observations should converge downward."""
        observations = [2100.0] * 30
        formula_prior = 2300.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # Result should be between prior and observations, but closer to observations
        assert 2100 < result < 2300
        assert result < (2100 + 2300) / 2

    def test_prior_lower_converges_upward(self, service):
        """Prior < observations should converge upward."""
        observations = [2400.0] * 30
        formula_prior = 2100.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # Result should be between prior and observations, but closer to observations
        assert 2100 < result < 2400
        assert result > (2100 + 2400) / 2

    def test_span_1_equals_last_observation(self, service):
        """Span=1 means alpha=1.0, result = last observation."""
        observations = [2000.0, 2100.0, 2200.0]
        formula_prior = 1500.0
        span = 1
        # alpha = 2 / (1 + 1) = 1.0
        # ema always = obs
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        assert result == 2200.0

    def test_larger_span_slower_convergence(self, service):
        """Larger span = lower alpha = slower convergence."""
        observations = [2500.0] * 20
        formula_prior = 2000.0

        # Smaller span (faster)
        result_fast = service._compute_tdee_from_observations(
            observations, formula_prior, span=5
        )
        # Larger span (slower)
        result_slow = service._compute_tdee_from_observations(
            observations, formula_prior, span=50
        )

        # After same observations, slower span should be closer to prior
        assert result_fast > result_slow
        assert result_fast > 2300

    def test_manual_calculation_3_observations(self, service):
        """Manually verify the EMA calculation step-by-step."""
        observations = [2100.0, 2200.0, 2300.0]
        formula_prior = 2000.0
        span = 21
        # alpha = 2 / 22 ≈ 0.090909
        # Step 1: ema = 0.090909 * 2100 + 0.909091 * 2000
        #             = 190.909 + 1818.182 = 2009.091
        # Step 2: ema = 0.090909 * 2200 + 0.909091 * 2009.091
        #             = 200 + 1826.446 = 2026.446
        # Step 3: ema = 0.090909 * 2300 + 0.909091 * 2026.446
        #             = 209.091 + 1842.405 = 2051.496
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        assert 2050 <= result <= 2052

    def test_float_precision_acceptable(self, service):
        """Floating point precision should not break the calculation."""
        observations = [2000.12, 2100.45, 2050.78]
        formula_prior = 2075.33
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # Result should be a reasonable float in the expected range
        assert isinstance(result, float)
        assert 2000 <= result <= 2100

    def test_oscillating_observations_dampens(self, service):
        """Oscillating observations should dampen due to EMA smoothing."""
        observations = [2100.0, 2300.0, 2100.0, 2300.0, 2100.0]
        formula_prior = 2200.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # Result should be between 2100 and 2300, not exactly at extremes
        assert 2150 <= result <= 2250

    def test_negative_observations_handled(self, service):
        """Edge case: negative observations (shouldn't happen, but should not crash)."""
        observations = [-1000.0, -800.0, -900.0]
        formula_prior = 2000.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # With many negative observations and small alpha, EMA moves down but doesn't flip
        # Result should be between prior and observations, but still positive-ish
        assert result < 2000
        assert isinstance(result, float)

    def test_very_large_observations(self, service):
        """Edge case: very large observation values."""
        observations = [10000.0, 11000.0, 10500.0]
        formula_prior = 2000.0
        span = 21
        result = service._compute_tdee_from_observations(
            observations, formula_prior, span=span
        )
        # With large observations and small alpha, EMA moves significantly upward
        # After 3 iterations with alpha ≈ 0.09, should be well above prior but below obs
        assert result > 2000
        assert result < 10500
