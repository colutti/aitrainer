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
