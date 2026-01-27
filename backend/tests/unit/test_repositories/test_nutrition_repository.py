
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import pymongo
from src.repositories.nutrition_repository import NutritionRepository
from src.api.models.nutrition_log import NutritionLog

class TestNutritionRepository(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        # Mock dictionary access for db['nutrition_logs']
        self.mock_db.__getitem__.return_value = self.mock_collection
        self.repo = NutritionRepository(self.mock_db)
        # Ensure repo.collection is our mock (in case BaseRepository sets it differently)
        self.repo.collection = self.mock_collection

    def test_ensure_indexes(self):
        self.repo.ensure_indexes()
        self.mock_collection.create_index.assert_called_with(
            [("user_email", pymongo.ASCENDING), ("date", pymongo.ASCENDING)],
            unique=True,
            name="unique_daily_log"
        )

    def test_save_log_new(self):
        log = NutritionLog(
            user_email="test@example.com",
            date=datetime(2024, 1, 1),
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
            meals=[]
        )
        
        # Mock update_one result for upsert (new doc)
        mock_result = MagicMock()
        mock_result.upserted_id = "new_id_123"
        self.mock_collection.update_one.return_value = mock_result
        
        doc_id, is_new = self.repo.save_log(log)
        
        self.assertEqual(doc_id, "new_id_123")
        self.assertTrue(is_new)
        self.mock_collection.update_one.assert_called_once()

    def test_save_log_existing(self):
        log = NutritionLog(
            user_email="test@example.com",
            date=datetime(2024, 1, 1),
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
            meals=[]
        )
        
        # Mock result for existing doc (no upserted_id)
        mock_result = MagicMock()
        mock_result.upserted_id = None
        self.mock_collection.update_one.return_value = mock_result
        
        # Mock find_one to return existing ID
        self.mock_collection.find_one.return_value = {"_id": "existing_id_456"}
        
        doc_id, is_new = self.repo.save_log(log)
        
        self.assertEqual(doc_id, "existing_id_456")
        self.assertFalse(is_new)

    def test_get_logs(self):
        # Setup mock cursor
        mock_cursor = MagicMock()
        mock_data = {
            "user_email": "test@example.com",
            "date": datetime(2024, 1, 1),
            "calories": 2000,
            "protein_grams": 100,
            "carbs_grams": 100,
            "fat_grams": 50,
            "meals": []
        }
        mock_cursor.__iter__.return_value = [mock_data]
        
        # Chain calls: find().sort().limit()
        self.mock_collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = self.repo.get_logs("test@example.com", limit=10)
        
        self.assertEqual(len(logs), 1)
        self.assertIsInstance(logs[0], NutritionLog)
        
        # Verify call chain
        self.mock_collection.find.assert_called_with({"user_email": "test@example.com"})
        self.mock_collection.find.return_value.sort.assert_called_with("date", pymongo.DESCENDING)
        self.mock_collection.find.return_value.sort.return_value.limit.assert_called_with(10)

    def test_get_logs_by_date_range(self):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 7)
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = []
        self.mock_collection.find.return_value.sort.return_value = mock_cursor
        
        self.repo.get_logs_by_date_range("test@example.com", start, end)
        
        # Check query structure for dates
        call_args = self.mock_collection.find.call_args
        query = call_args[0][0]
        self.assertEqual(query["user_email"], "test@example.com")
        self.assertIn("$gte", query["date"])
        self.assertIn("$lte", query["date"])

    def test_get_paginated(self):
        # Mock count
        self.mock_collection.count_documents.return_value = 50
        
        # Mock cursor for data
        mock_cursor = MagicMock()
        mock_doc = {"_id": "abc", "date": datetime(2024, 1, 1), "calories": 2000}
        mock_cursor.__iter__.return_value = [mock_doc]
        
        # Chain: find().sort().skip().limit()
        self.mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        
        logs, total = self.repo.get_paginated("test@example.com", page=2, page_size=10)
        
        self.assertEqual(total, 50)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["id"], "abc")  # _id transformed to id
        self.assertNotIn("_id", logs[0])
        
        # Verify skip calc: page 2, size 10 -> skip 10
        self.mock_collection.find.return_value.sort.return_value.skip.assert_called_with(10)

    def test_get_stats_empty(self):
        """Test get_stats with no data."""
        self.mock_collection.find.return_value.sort.return_value = []
        self.mock_collection.count_documents.return_value = 0
        
        stats = self.repo.get_stats("test@example.com")
        
        self.assertIsNone(stats.today)
        self.assertEqual(stats.total_logs, 0)
        self.assertEqual(len(stats.last_7_days), 7)
        self.assertEqual(stats.avg_daily_calories, 0)

    def test_get_stats_with_data(self):
        now = datetime.now()
        mock_logs = [
            {
                "_id": "1",
                "user_email": "test@example.com",
                "date": now,
                "calories": 2500,
                "protein_grams": 200,
                "carbs_grams": 250,
                "fat_grams": 80,
                "meals": []
            },
            {
                "_id": "2",
                "user_email": "test@example.com",
                "date": now - timedelta(days=1),
                "calories": 2000,
                "protein_grams": 150,
                "carbs_grams": 200,
                "fat_grams": 60,
                "meals": []
            }
        ]
        
        # Need to return iterator so list() works
        self.mock_collection.find.return_value.sort.return_value = iter(mock_logs)
        self.mock_collection.count_documents.return_value = 2
        
        stats = self.repo.get_stats("test@example.com")
        
        self.assertIsNotNone(stats.today)
        self.assertEqual(stats.today.calories, 2500)
        self.assertEqual(stats.total_logs, 2)
        # Check averages:
        # 7 days: (2500 + 2000) / 2 = 2250
        # 14 days: (2500 + 2000) / 2 = 2250 (since we only have 2 logs in the range)
        self.assertEqual(stats.avg_daily_calories, 2250)
        self.assertEqual(stats.avg_daily_calories_14_days, 2250)

