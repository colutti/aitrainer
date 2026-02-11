"""
Tests for database weight operations in MongoDatabase service.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta

from src.api.models.weight_log import WeightLog
from src.services.database import MongoDatabase

class TestWeightDbInteractions:
    @pytest.fixture
    def db(self):
        with patch("src.services.database.pymongo.MongoClient") as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            service = MongoDatabase()
            yield service

    def test_save_weight_log_success(self, db):
        """Save log with body composition fields and retrieve."""
        log = WeightLog(
            user_email="test@test.com",
            date=date.today(),
            weight_kg=76.8,
            body_fat_pct=24.2,
            source="scale_import",
        )
        db.weight.collection.update_one.return_value.upserted_id = "new_id_123"

        doc_id, is_new = db.save_weight_log(log)
        assert is_new is True
        assert doc_id == "new_id_123"
        db.weight.collection.update_one.assert_called_once()

    def test_get_weight_logs_success(self, db):
        """Verify get_weight_logs returns list of WeightLog objects."""
        mock_docs = [
            {
                "user_email": "test@test.com",
                "date": datetime(2026, 1, 10, 0, 0, 0),
                "weight_kg": 80.5,
                "_id": "id1",
            }
        ]
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor

        logs = db.get_weight_logs("test@test.com")
        assert len(logs) == 1
        assert logs[0].weight_kg == 80.5

    def test_delete_weight_log_success(self, db):
        """Verify delete returns True when document is deleted."""
        db.weight.collection.delete_one.return_value.deleted_count = 1
        result = db.delete_weight_log("test@test.com", date(2026, 1, 10))
        assert result is True

    def test_get_by_date_range(self, db):
        """Date range query works correctly."""
        mock_doc = {
            "user_email": "range@test.com",
            "date": datetime.now(),
            "weight_kg": 78.0,
            "_id": "some_id",
        }
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = [mock_doc]
        db.weight.collection.find.return_value.sort.return_value = mock_cursor

        logs = db.get_weight_logs_by_date_range(
            "range@test.com", date.today() - timedelta(days=10), date.today()
        )
        assert len(logs) == 1
        assert logs[0].weight_kg == 78.0
