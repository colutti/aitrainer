import unittest
from unittest.mock import MagicMock, patch
from src.services.database import MongoDatabase
import pymongo
from typing import cast


class TestDatabaseWorkouts(unittest.TestCase):
    @patch("src.services.database.pymongo.MongoClient")
    def setUp(self, mock_client):
        # Mock client and db init
        self.mock_mongo_client = MagicMock()
        mock_client.return_value = self.mock_mongo_client
        self.db = MongoDatabase()
        # Access the collection mock directly from the repository
        self.mock_collection = cast(MagicMock, self.db.workouts_repo.collection)

    def test_get_workouts_paginated_query_construction(self):
        """Verify query filters and pagination logic."""
        # Setup count return
        self.mock_collection.count_documents.return_value = 50

        # Setup find cursor mock
        mock_cursor = MagicMock()
        self.mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter(
            [
                {
                    "_id": "1",
                    "user_email": "test@test.com",
                    "workout_type": "Legs",
                    "exercises": [],
                    "date": "2024-01-01",
                }
            ]
        )

        # Call the method
        workouts, total = self.db.get_workouts_paginated(
            "test@test.com", page=2, page_size=10, workout_type="Legs"
        )

        # Verify count query includes type
        expected_query = {"user_email": "test@test.com", "workout_type": "Legs"}
        self.mock_collection.count_documents.assert_called_with(expected_query)

        # Verify find arguments
        self.mock_collection.find.assert_called_with(expected_query)

        # Verify pagination chain
        mock_cursor.sort.assert_called_with("date", pymongo.DESCENDING)
        mock_cursor.skip.assert_called_with(10)  # (Page 2 - 1) * 10
        mock_cursor.limit.assert_called_with(10)

        self.assertEqual(total, 50)
        self.assertEqual(len(workouts), 1)

    def test_get_workouts_paginated_no_filter(self):
        """Verify query when no filter provided."""
        self.mock_collection.count_documents.return_value = 5
        mock_cursor = MagicMock()
        self.mock_collection.find.return_value = mock_cursor
        # Necessary to mock method chaining
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.__iter__.return_value = iter([])

        self.db.get_workouts_paginated("test@test.com")

        # Expect only user_email in query
        expected_query = {"user_email": "test@test.com"}
        self.mock_collection.count_documents.assert_called_with(expected_query)

    def test_get_workout_types(self):
        """Verify getting distinct types."""
        self.mock_collection.distinct.return_value = ["Push", "Pull", None, ""]

        types = self.db.get_workout_types("test@test.com")

        self.mock_collection.distinct.assert_called_with(
            "workout_type", {"user_email": "test@test.com"}
        )

        # Should filter out None/Empty and sort
        self.assertEqual(types, ["Pull", "Push"])
