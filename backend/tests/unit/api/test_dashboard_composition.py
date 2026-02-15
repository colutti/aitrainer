from datetime import datetime
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.models.weight_log import WeightLog
from src.core.deps import get_mongo_database
from src.services.auth import verify_token

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def client(mock_db):
    app.dependency_overrides[get_mongo_database] = lambda: mock_db
    app.dependency_overrides[verify_token] = lambda: "test@example.com"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

def test_body_composition_persistence_on_dashboard(client, mock_db):
    """
    Test that BF%, Muscle%, and BMR are pulled from history
    if the latest log doesn't have them.
    """
    email = "test@example.com"

    # Yesterday's log with full composition
    yesterday = datetime(2026, 2, 8)
    log_yesterday = WeightLog(
        user_email=email,
        date=yesterday.date(),
        weight_kg=80.0,
        body_fat_pct=15.0,
        muscle_mass_pct=40.0,
        bmr=1800
    )

    # Today's log with only weight
    today = datetime(2026, 2, 9)
    log_today = WeightLog(
        user_email=email,
        date=today.date(),
        weight_kg=81.0,
        body_fat_pct=None,
        muscle_mass_pct=None,
        bmr=None
    )

    # Return logs in descending order (latest first)
    mock_db.get_weight_logs.return_value = [log_today, log_yesterday]
    mock_db.get_weight_logs_by_date_range.return_value = [log_today, log_yesterday]

    # Stub other methods to avoid crashes
    mock_db.get_nutrition_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs.return_value = []
    mock_db.get_workout_logs.return_value = []
    mock_db.get_user_profile.return_value = None

    # Mocking WorkoutRepository within the endpoint
    with patch('src.api.endpoints.dashboard.WorkoutRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_stats.return_value = MagicMock(
            current_streak_weeks=0,
            recent_prs=[],
            strength_radar={},
            volume_trend=[],
            weekly_frequency=[],
            last_workout=None
        )

        # ACT
        response = client.get("/dashboard")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        body = data["stats"]["body"]

        # Desired behavior: should use 15.0, 40.0, 1800 from yesterday
        assert body["body_fat_pct"] == 15.0
        assert body["muscle_mass_pct"] == 40.0
        assert body["bmr"] == 1800


def test_fat_and_muscle_diff_calculated_for_7_day_period(client, mock_db):
    """
    Test that fat_diff and muscle_diff are calculated for 7-day period,
    similar to weight_diff.
    """
    email = "test@example.com"

    # 7 days ago with composition data
    seven_days_ago = datetime(2026, 2, 2)
    log_old = WeightLog(
        user_email=email,
        date=seven_days_ago.date(),
        weight_kg=80.0,
        body_fat_pct=20.0,
        muscle_mass_pct=38.0,
        bmr=1800
    )

    # Today with updated composition
    today = datetime(2026, 2, 9)
    log_today = WeightLog(
        user_email=email,
        date=today.date(),
        weight_kg=79.5,
        body_fat_pct=19.0,
        muscle_mass_pct=39.0,
        bmr=1800
    )

    # Return logs in descending order (latest first)
    mock_db.get_weight_logs.return_value = [log_today, log_old]
    mock_db.get_weight_logs_by_date_range.return_value = [log_today, log_old]

    # Stub other methods to avoid crashes
    mock_db.get_nutrition_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs.return_value = []
    mock_db.get_workout_logs.return_value = []
    mock_db.get_user_profile.return_value = None

    # Mocking WorkoutRepository within the endpoint
    with patch('src.api.endpoints.dashboard.WorkoutRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_stats.return_value = MagicMock(
            current_streak_weeks=0,
            recent_prs=[],
            strength_radar={},
            volume_trend=[],
            weekly_frequency=[],
            last_workout=None
        )

        # Mock _get_today() to match test date
        with patch('src.api.endpoints.dashboard._get_today', return_value=today):
            # ACT
            response = client.get("/dashboard")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        body = data["stats"]["body"]

        # Should calculate differences: current - 7_days_ago
        assert body["fat_diff"] == -1.0  # 19.0 - 20.0
        assert body["muscle_diff"] == 1.0  # 39.0 - 38.0


def test_composition_diffs_for_multiple_periods(client, mock_db):
    """
    Test that fat_diff, muscle_diff, and weight_diff are calculated
    for 7, 15, and 30-day periods.
    """
    email = "test@example.com"

    # 30 days ago
    thirty_days_ago = datetime(2026, 1, 10)
    log_30d = WeightLog(
        user_email=email,
        date=thirty_days_ago.date(),
        weight_kg=82.0,
        body_fat_pct=22.0,
        muscle_mass_pct=36.0,
        bmr=1800
    )

    # 15 days ago
    fifteen_days_ago = datetime(2026, 1, 25)
    log_15d = WeightLog(
        user_email=email,
        date=fifteen_days_ago.date(),
        weight_kg=80.5,
        body_fat_pct=20.5,
        muscle_mass_pct=37.5,
        bmr=1800
    )

    # 7 days ago
    seven_days_ago = datetime(2026, 2, 2)
    log_7d = WeightLog(
        user_email=email,
        date=seven_days_ago.date(),
        weight_kg=80.0,
        body_fat_pct=20.0,
        muscle_mass_pct=38.0,
        bmr=1800
    )

    # Today
    today = datetime(2026, 2, 9)
    log_today = WeightLog(
        user_email=email,
        date=today.date(),
        weight_kg=79.5,
        body_fat_pct=19.0,
        muscle_mass_pct=39.0,
        bmr=1800
    )

    # Return logs in descending order (latest first)
    mock_db.get_weight_logs.return_value = [log_today, log_7d, log_15d, log_30d]
    mock_db.get_weight_logs_by_date_range.return_value = [log_today, log_7d, log_15d, log_30d]

    # Stub other methods to avoid crashes
    mock_db.get_nutrition_logs_by_date_range.return_value = []
    mock_db.get_nutrition_logs.return_value = []
    mock_db.get_workout_logs.return_value = []
    mock_db.get_user_profile.return_value = None

    # Mocking WorkoutRepository within the endpoint
    with patch('src.api.endpoints.dashboard.WorkoutRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_stats.return_value = MagicMock(
            current_streak_weeks=0,
            recent_prs=[],
            strength_radar={},
            volume_trend=[],
            weekly_frequency=[],
            last_workout=None
        )

        # Mock _get_today() to match test date
        with patch('src.api.endpoints.dashboard._get_today', return_value=today):
            # ACT
            response = client.get("/dashboard")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        body = data["stats"]["body"]

        # Weight diffs
        assert body["weight_diff"] == -0.5  # 79.5 - 80.0
        assert body["weight_diff_15"] == -1.0  # 79.5 - 80.5
        assert body["weight_diff_30"] == -2.5  # 79.5 - 82.0

        # Fat diffs
        assert body["fat_diff"] == -1.0  # 19.0 - 20.0
        assert body["fat_diff_15"] == -1.5  # 19.0 - 20.5
        assert body["fat_diff_30"] == -3.0  # 19.0 - 22.0

        # Muscle diffs
        assert body["muscle_diff"] == 1.0  # 39.0 - 38.0
        assert body["muscle_diff_15"] == 1.5  # 39.0 - 37.5
        assert body["muscle_diff_30"] == 3.0  # 39.0 - 36.0
