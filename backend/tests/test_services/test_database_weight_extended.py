"""
Extended tests for database weight operations.
Tests for get_weight_logs() and delete_weight_log() which were previously untested.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
import pymongo

from src.api.models.weight_log import WeightLog
from src.services.database import MongoDatabase


class TestGetWeightLogs:
    """Tests for get_weight_logs() method."""
    
    @pytest.fixture
    def db(self):
        with patch('src.services.database.pymongo.MongoClient') as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            
            service = MongoDatabase()
            # The repository is already initialized in MongoDatabase.__init__
            # We configure the collection mock inside the repository
            # service.weight.collection is the magic mock returned by mock_db_instance["weight_logs"]
            
            yield service

    def test_get_weight_logs_returns_weight_log_objects(self, db):
        """Verify get_weight_logs returns list of WeightLog objects."""
        mock_docs = [
            {
                "user_email": "test@test.com",
                "date": datetime(2026, 1, 10, 0, 0, 0),
                "weight_kg": 80.5,
                "body_fat_pct": 22.0,
                "_id": "id1"
            },
            {
                "user_email": "test@test.com",
                "date": datetime(2026, 1, 9, 0, 0, 0),
                "weight_kg": 81.0,
                "_id": "id2"
            }
        ]
        
        # Mock the chain: find().sort().limit()
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = db.get_weight_logs("test@test.com")
        
        assert len(logs) == 2
        assert all(isinstance(log, WeightLog) for log in logs)
        assert logs[0].weight_kg == 80.5
        assert logs[0].body_fat_pct == 22.0
        assert logs[1].weight_kg == 81.0

    def test_get_weight_logs_converts_datetime_to_date(self, db):
        """Verify datetime from DB is converted to date object."""
        mock_docs = [{
            "user_email": "test@test.com",
            "date": datetime(2026, 1, 15, 10, 30, 0),  # datetime with time
            "weight_kg": 75.0,
            "_id": "id1"
        }]
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = db.get_weight_logs("test@test.com")
        
        assert len(logs) == 1
        assert isinstance(logs[0].date, date)
        assert logs[0].date == date(2026, 1, 15)

    def test_get_weight_logs_respects_limit(self, db):
        """Verify limit parameter is passed to MongoDB query."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        db.get_weight_logs("test@test.com", limit=10)
        
        db.weight.collection.find.return_value.sort.return_value.limit.assert_called_with(10)

    def test_get_weight_logs_sorts_descending(self, db):
        """Verify logs are sorted by date descending."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        db.get_weight_logs("test@test.com")
        
        db.weight.collection.find.return_value.sort.assert_called_with("date", pymongo.DESCENDING)

    def test_get_weight_logs_empty_result(self, db):
        """Verify empty user returns empty list without error."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = db.get_weight_logs("nonexistent@test.com")
        
        assert logs == []
        assert isinstance(logs, list)

    def test_get_weight_logs_filters_by_user_email(self, db):
        """Verify query filters by user_email."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.weight.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        db.get_weight_logs("specific@test.com")
        
        db.weight.collection.find.assert_called_with({"user_email": "specific@test.com"})


class TestDeleteWeightLog:
    """Tests for delete_weight_log() method."""
    
    @pytest.fixture
    def db(self):
        with patch('src.services.database.pymongo.MongoClient') as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            
            service = MongoDatabase()
            yield service

    def test_delete_weight_log_success(self, db):
        """Verify delete returns True when document is deleted."""
        db.weight.collection.delete_one.return_value.deleted_count = 1
        
        result = db.delete_weight_log("test@test.com", date(2026, 1, 10))
        
        assert result is True

    def test_delete_weight_log_not_found(self, db):
        """Verify delete returns False when document doesn't exist."""
        db.weight.collection.delete_one.return_value.deleted_count = 0
        
        result = db.delete_weight_log("test@test.com", date(2026, 1, 10))
        
        assert result is False

    def test_delete_weight_log_uses_datetime_for_query(self, db):
        """Verify date is converted to datetime for MongoDB query."""
        db.weight.collection.delete_one.return_value.deleted_count = 1
        
        db.delete_weight_log("test@test.com", date(2026, 1, 15))
        
        call_args = db.weight.collection.delete_one.call_args[0][0]
        assert call_args["user_email"] == "test@test.com"
        assert call_args["date"] == datetime(2026, 1, 15, 0, 0, 0)

    def test_delete_weight_log_correct_query_structure(self, db):
        """Verify delete_one is called with correct query."""
        db.weight.collection.delete_one.return_value.deleted_count = 1
        
        db.delete_weight_log("user@example.com", date(2026, 6, 20))
        
        db.weight.collection.delete_one.assert_called_once()
        query = db.weight.collection.delete_one.call_args[0][0]
        assert "user_email" in query
        assert "date" in query
