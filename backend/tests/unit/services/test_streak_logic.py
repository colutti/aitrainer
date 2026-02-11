from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pytest
from src.repositories.workout_repository import WorkoutRepository

@pytest.fixture
def repo():
    db = MagicMock()
    # Mock collection for the constructor
    db.workout_logs = MagicMock()
    return WorkoutRepository(db)

def test_streak_calculation_on_monday(repo):
    """
    Test that streak correctly identifies that the current week is in progress
    and doesn't reset to 0 on Monday if the previous week was successful.
    """
    # 1. Setup Data
    # Current date: Monday, Feb 9, 2026
    now = datetime(2026, 2, 9, 10, 0, 0)
    
    # Previous week was week 6 (Feb 2-8). 
    # Let's say user did 4 workouts in week 6.
    week_6_date = datetime(2026, 2, 4, 12, 0, 0) # Wednesday in week 6
    
    workouts = [
        {"date": week_6_date, "workout_type": "Push", "_id": "1"},
        {"date": week_6_date + timedelta(hours=1), "workout_type": "Pull", "_id": "2"},
        {"date": week_6_date + timedelta(days=1), "workout_type": "Legs", "_id": "3"},
        {"date": week_6_date + timedelta(days=2), "workout_type": "Push", "_id": "4"},
    ]
    
    # 2. Mock and Execute
    with patch('src.repositories.workout_repository.datetime') as mock_datetime:
        mock_datetime.now.return_value = now
        # Mock fromisocalendar if needed (it is used in the loop)
        mock_datetime.fromisocalendar.side_effect = datetime.fromisocalendar
        
        # We need to pass the workouts to the internal calculation method
        streak = repo._calculate_weekly_streak(workouts)
        
        # 3. Assert
        # Current implementation will start at (2026, 7). 
        # (2026, 7) has 0 workouts -> streak stops immediately -> streak = 0.
        # Desired: streak should be 1 because week 6 was successful and week 7 is not over.
        assert streak == 1, f"Expected streak of 1, got {streak}. (Monday morning scenario)"
