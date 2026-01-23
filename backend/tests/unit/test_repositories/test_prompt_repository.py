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

    def test_log_prompt_inserts_and_trims_with_pydantic(self):
        # Setup mock for find().sort().limit()
        mock_cursor = MagicMock()
        self.mock_collection.find.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.limit.return_value = []

        # Create a dummy Pydantic-like object (or use a real one if simple)
        from pydantic import BaseModel
        class DummyModel(BaseModel):
            name: str
            val: int

        data = {"model": DummyModel(name="test", val=123)}

        # Call log_prompt
        self.repo.log_prompt("test@user.com", data, max_logs=2)

        # Verify insert - should have converted to dict
        self.mock_collection.insert_one.assert_called_once()
        inserted_doc = self.mock_collection.insert_one.call_args[0][0]
        self.assertEqual(inserted_doc["prompt"]["model"], {"name": "test", "val": 123})

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
