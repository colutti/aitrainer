import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock
from src.repositories.prompt_repository import PromptRepository

class TestPromptRepository(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_collection = MagicMock()
        self.mock_db.__getitem__.return_value = self.mock_collection
        self.repo = PromptRepository(self.mock_db)

    def test_log_prompt_inserts_and_trims(self):
        # Setup mock for find().sort().limit()
        mock_cursor = MagicMock()
        self.mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [
            {"_id": "id1", "timestamp": datetime.now(timezone.utc)},
            {"_id": "id2", "timestamp": datetime.now(timezone.utc)},
        ]

        # Call log_prompt with max_logs=2
        self.repo.log_prompt("test@user.com", {"data": "test"}, max_logs=2)

        # Verify insert
        self.mock_collection.insert_one.assert_called_once()
        args = self.mock_collection.insert_one.call_args[0][0]
        self.assertEqual(args["user_email"], "test@user.com")
        self.assertEqual(args["prompt"], {"data": "test"})

        # Verify limit check and deletion of old logs
        self.mock_collection.find.assert_called_with({"user_email": "test@user.com"})
        self.mock_collection.delete_many.assert_called_once()
        del_args = self.mock_collection.delete_many.call_args[0][0]
        self.assertEqual(del_args["user_email"], "test@user.com")
        self.assertIn("$nin", del_args["_id"])
        self.assertEqual(del_args["_id"]["$nin"], ["id1", "id2"])

    def test_get_user_prompts(self):
        mock_cursor = MagicMock()
        self.mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = [{"_id": "id1"}]

        results = self.repo.get_user_prompts("test@user.com", limit=5)
        
        self.assertEqual(len(results), 1)
        self.mock_collection.find.assert_called_with({"user_email": "test@user.com"})
        mock_cursor.sort.assert_called_with("timestamp", -1)
        mock_cursor.limit.assert_called_with(5)
