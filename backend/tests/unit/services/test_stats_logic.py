import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.repositories.workout_repository import WorkoutRepository


class TestStatsLogic(unittest.TestCase):
    def setUp(self):
        # Mock the database and collection
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.__getitem__.return_value = self.mock_collection

        # Initialize Repository with mocked DB
        self.repo = WorkoutRepository(self.mock_db)

    def test_calculate_weekly_streak_empty(self):
        """Verifies streak is 0 for empty history."""
        self.assertEqual(self.repo._calculate_weekly_streak([]), 0)

    def test_calculate_weekly_streak_current_week(self):
        """Verifies streak logic for current week activity (>=3 workouts)."""
        today = datetime.now()
        workouts = [
            {"date": today},
            {"date": today},
            {"date": today},
        ]
        # 1 week active (current)
        self.assertEqual(self.repo._calculate_weekly_streak(workouts), 1)

    def test_calculate_weekly_streak_not_enough_workouts(self):
        """Verifies streak does not incement if < 3 workouts in a week."""
        today = datetime.now()
        workouts = [
            {"date": today},
            {"date": today},
            # Only 2 workouts
        ]
        self.assertEqual(self.repo._calculate_weekly_streak(workouts), 0)

    def test_calculate_recent_prs_absolute_max(self):
        """
        Verifies that the PR logic finds the ABSOLUTE maximum weight,
        not just the max from the most recent workout.
        """
        workouts = [
            # Workout 3 (Jan 15): 90kg (Strong, but not PR)
            {
                "_id": "id_jan15",
                "date": datetime(2024, 1, 15),
                "exercises": [
                    {"name": "Squat", "weights_per_set": [90], "reps_per_set": [5]}
                ],
            },
            # Workout 2 (Jan 10): 100kg (The PR!)
            {
                "_id": "id_jan10",
                "date": datetime(2024, 1, 10),
                "exercises": [
                    {"name": "Squat", "weights_per_set": [100], "reps_per_set": [1]}
                ],
            },
            # Workout 1 (Jan 1): 80kg (Baseline)
            {
                "_id": "id_jan1",
                "date": datetime(2024, 1, 1),
                "exercises": [
                    {"name": "Squat", "weights_per_set": [80], "reps_per_set": [5]}
                ],
            },
        ]

        prs = self.repo._calculate_recent_prs(workouts, limit=5)

        self.assertEqual(len(prs), 1)
        record = prs[0]

        # Should be 100kg from Jan 10
        self.assertEqual(record.exercise_name, "Squat")
        self.assertEqual(record.weight, 100)
        self.assertEqual(record.date, datetime(2024, 1, 10))

    def test_calculate_recent_prs_multiple_exercises(self):
        """Verifies PRs are tracked independently for different exercises."""
        workouts = [
            # Jan 5: Deadlift PR
            {
                "_id": "id_jan5",
                "date": datetime(2024, 1, 5),
                "exercises": [
                    {"name": "Deadlift", "weights_per_set": [150], "reps_per_set": [1]}
                ],
            },
            # Jan 1: Bench PR
            {
                "_id": "id_jan1",
                "date": datetime(2024, 1, 1),
                "exercises": [
                    {"name": "Bench", "weights_per_set": [100], "reps_per_set": [1]}
                ],
            },
        ]

        prs = self.repo._calculate_recent_prs(workouts, limit=5)

        # Should have 2 records
        self.assertEqual(len(prs), 2)

        # Sorted by date Descending (Deadlift Jan 5 is simpler/newer)
        self.assertEqual(prs[0].exercise_name, "Deadlift")
        self.assertEqual(prs[0].weight, 150)

        self.assertEqual(prs[1].exercise_name, "Bench")
        self.assertEqual(prs[1].weight, 100)

    def test_calculate_weekly_metrics(self):
        """Verifies calculation of weekly frequency and volume."""
        # Setup:
        # Monday: Chest (1000kg)
        # Wednesday: Legs (2000kg)

        # Create a mock Monday date
        # If today is Monday(0), then Monday is today.
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())  # Monday
        wednesday = start_of_week + timedelta(days=2)  # Wednesday

        workouts = [
            {
                "date": start_of_week,
                "workout_type": "Chest",
                "exercises": [
                    {
                        "name": "Bench",
                        "weights_per_set": [100],
                        "reps_per_set": [10],
                    }  # 1000 volume
                ],
            },
            {
                "date": wednesday,
                "workout_type": "Legs",
                "exercises": [
                    {
                        "name": "Squat",
                        "weights_per_set": [100, 100],
                        "reps_per_set": [10, 10],
                    }  # 2000 volume
                ],
            },
        ]

        freq, volumes = self.repo._calculate_weekly_metrics(workouts)

        # Frequency: Mon(0) and Wed(2) should be True
        self.assertTrue(freq[0])  # Monday
        self.assertTrue(freq[2])  # Wednesday
        self.assertFalse(freq[1])  # Tuesday

        # Volume
        # Chest: 1000, Legs: 2000
        chest_vol = next((v for v in volumes if v.category == "Chest"), None)
        legs_vol = next((v for v in volumes if v.category == "Legs"), None)

        self.assertIsNotNone(chest_vol)
        assert chest_vol is not None
        self.assertEqual(chest_vol.volume, 1000)

        self.assertIsNotNone(legs_vol)
        assert legs_vol is not None
        self.assertEqual(legs_vol.volume, 2000)
