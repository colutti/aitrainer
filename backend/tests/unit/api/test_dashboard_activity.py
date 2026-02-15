from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from src.api.endpoints.dashboard import get_dashboard_data
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.workout_log import WorkoutWithId

def test_recent_activity_filters_and_duplicates():
    """
    Test that recent activity:
    1. Includes nutrition logs from yesterday.
    2. Does not include duplicate workout entries.
    """
    email = "test@example.com"
    today_dt = datetime(2026, 2, 9, 12, 0, 0)
    yesterday_dt = today_dt - timedelta(days=1)

    # 1. Mock DB
    mock_db = MagicMock()

    # Nutrition from yesterday - THIS SHOULD BE INCLUDED
    nut1 = NutritionLog(user_email=email, date=yesterday_dt, calories=2500, protein_grams=150, carbs_grams=250, fat_grams=80)
    mock_db.get_nutrition_logs.return_value = [nut1]
    mock_db.get_nutrition_logs_by_date_range.return_value = []

    # Weight from today
    w1 = WeightLog(user_email=email, date=today_dt.date(), weight_kg=80.0)
    mock_db.get_weight_logs.return_value = [w1]
    mock_db.get_weight_logs_by_date_range.return_value = [w1]

    # Mocking WorkoutRepository within the endpoint
    with patch('src.api.endpoints.dashboard.WorkoutRepository') as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Duplicate workouts
        work1 = WorkoutWithId(id="work1", user_email=email, date=yesterday_dt, workout_type="Push", exercises=[])
        mock_db.get_workout_logs.return_value = [work1, work1]

        mock_repo.get_stats.return_value = MagicMock(
            current_streak_weeks=0,
            recent_prs=[],
            strength_radar={},
            volume_trend=[],
            weekly_frequency=[],
            last_workout=None
        )

        # Mock AdaptiveTDEEService
        with patch('src.api.endpoints.dashboard.AdaptiveTDEEService') as mock_tdee_class:
            mock_tdee = MagicMock()
            mock_tdee_class.return_value = mock_tdee
            mock_tdee.calculate_tdee.return_value = {"tdee": 2500, "daily_target": 2500, "goal_type": "maintain", "consistency_score": 100}

            # 2. ACT
            response = get_dashboard_data(user_email=email, db=mock_db)

            # 3. ASSERT
            activities = response.recentActivities

            # Check Nutrition included
            nutrition_activities = [a for a in activities if a.type == "nutrition"]
            assert len(nutrition_activities) > 0, "Nutrition from yesterday should be included"

            # Check Workouts unique
            workout_activities = [a for a in activities if a.type == "workout"]
            # If we return [work1, work1], it should be deduplicated
            assert len(workout_activities) == 1, f"Workouts should be unique, found {len(workout_activities)}"


def test_recent_activity_dates_formatted_as_dd_mm_yyyy():
    """
    Test that recent activity dates are formatted as DD/MM/YYYY (Brazilian format),
    without time component.
    """
    email = "test@example.com"
    today_dt = datetime(2026, 2, 15, 14, 30, 45)  # Specific time to verify it's stripped

    # 1. Mock DB
    mock_db = MagicMock()

    # Workout with time
    work1 = WorkoutWithId(id="work1", user_email=email, date=today_dt, workout_type="Push", exercises=[], duration_minutes=60)
    mock_db.get_workout_logs.return_value = [work1]
    mock_db.get_nutrition_logs.return_value = []
    mock_db.get_weight_logs.return_value = []
    mock_db.get_nutrition_logs_by_date_range.return_value = []

    # Mocking WorkoutRepository
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

        # Mock AdaptiveTDEEService
        with patch('src.api.endpoints.dashboard.AdaptiveTDEEService') as mock_tdee_class:
            mock_tdee = MagicMock()
            mock_tdee_class.return_value = mock_tdee
            mock_tdee.calculate_tdee.return_value = {"tdee": 2500, "daily_target": 2500, "goal_type": "maintain", "consistency_score": 100}

            # 2. ACT
            response = get_dashboard_data(user_email=email, db=mock_db)

            # 3. ASSERT
            activities = response.recentActivities
            assert len(activities) > 0, "Should have activities"

            # Check date format: DD/MM/YYYY (e.g., "15/02/2026")
            import re
            date_pattern = r'^\d{2}/\d{2}/\d{4}$'

            for activity in activities:
                assert re.match(date_pattern, activity.date), \
                    f"Date '{activity.date}' should be in DD/MM/YYYY format, got '{activity.date}'"
                # Verify no time component
                assert ' ' not in activity.date, \
                    f"Date '{activity.date}' should not contain time component"
                # Verify expected date
                assert activity.date == "15/02/2026", \
                    f"Expected date '15/02/2026', got '{activity.date}'"
