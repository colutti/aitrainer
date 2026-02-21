import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.api.models.weight_log import WeightLog
from src.services.database import MongoDatabase


# Mock the NutritionLog since it's used in the service but we don't need its logic for the weight filter test
class MockNutritionLog:
    def __init__(self, date_obj, calories):
        self.date = datetime(date_obj.year, date_obj.month, date_obj.day)
        self.calories = calories




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
