"""
Tests for database nutrition operations.
Tests for get_nutrition_logs(), get_nutrition_paginated(), and related methods.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
import pymongo

from src.api.models.nutrition_log import NutritionLog
from src.services.database import MongoDatabase


class TestGetNutritionLogs:
    """Tests for get_nutrition_logs() method."""
    
    @pytest.fixture
    def db(self):
        with patch('src.services.database.pymongo.MongoClient') as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            
            service = MongoDatabase()
            # The repository is already initialized in MongoDatabase.__init__
            
            yield service

    def test_get_nutrition_logs_returns_list(self, db):
        """Verify get_nutrition_logs returns list of NutritionLog objects."""
        mock_docs = [
            {
                "user_email": "test@test.com",
                "date": datetime(2026, 1, 10),
                "calories": 2000,
                "protein_grams": 150,
                "carbs_grams": 200,
                "fat_grams": 70
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.nutrition.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = db.get_nutrition_logs("test@test.com")
        
        assert len(logs) == 1
        assert isinstance(logs[0], NutritionLog)
        assert logs[0].calories == 2000

    def test_get_nutrition_logs_empty_result(self, db):
        """Verify empty user returns empty list."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        logs = db.get_nutrition_logs("nonexistent@test.com")
        
        assert logs == []

    def test_get_nutrition_logs_sorts_descending(self, db):
        """Verify logs are sorted by date descending."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        db.get_nutrition_logs("test@test.com")
        
        db.nutrition.collection.find.return_value.sort.assert_called_with("date", pymongo.DESCENDING)

    def test_get_nutrition_logs_respects_limit(self, db):
        """Verify limit parameter is passed correctly."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value.limit.return_value = mock_cursor
        
        db.get_nutrition_logs("test@test.com", limit=15)
        
        db.nutrition.collection.find.return_value.sort.return_value.limit.assert_called_with(15)


class TestGetNutritionPaginated:
    """Tests for get_nutrition_paginated() method."""
    
    @pytest.fixture
    def db(self):
        with patch('src.services.database.pymongo.MongoClient') as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            
            service = MongoDatabase()
            
            yield service

    def test_get_nutrition_paginated_returns_list_and_total(self, db):
        """Verify returns tuple of (list, total)."""
        mock_docs = [
            {"_id": "id1", "user_email": "test@test.com", "date": datetime.now(), "calories": 2000}
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.nutrition.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        db.nutrition.collection.count_documents.return_value = 25
        
        logs, total = db.get_nutrition_paginated("test@test.com", page=1, page_size=10)
        
        assert total == 25
        assert isinstance(logs, list)
        assert len(logs) == 1
        assert logs[0]["id"] == "id1"

    def test_get_nutrition_paginated_calculates_skip_correctly(self, db):
        """Verify skip is calculated correctly for pagination."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        db.nutrition.collection.count_documents.return_value = 0
        
        # Page 3 with page_size 10 should skip 20
        db.get_nutrition_paginated("test@test.com", page=3, page_size=10)
        
        db.nutrition.collection.find.return_value.sort.return_value.skip.assert_called_with(20)

    def test_get_nutrition_paginated_with_days_filter(self, db):
        """Verify days filter adds date constraint to query."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        db.nutrition.collection.count_documents.return_value = 0
        
        db.get_nutrition_paginated("test@test.com", days=7)
        
        # Verify the query includes a date filter
        call_args = db.nutrition.collection.find.call_args[0][0]
        assert "date" in call_args
        assert "$gte" in call_args["date"]


class TestGetNutritionLogsByDateRange:
    """Tests for get_nutrition_logs_by_date_range() method."""
    
    @pytest.fixture
    def db(self):
        with patch('src.services.database.pymongo.MongoClient') as mock_client:
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance
            
            service = MongoDatabase()
            
            yield service

    def test_get_by_date_range_returns_logs(self, db):
        """Verify date range query returns NutritionLog objects."""
        mock_docs = [
            {
                "user_email": "test@test.com",
                "date": datetime(2026, 1, 10),
                "calories": 1800,
                "protein_grams": 120,
                "carbs_grams": 180,
                "fat_grams": 60
            }
        ]
        
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter(mock_docs)
        db.nutrition.collection.find.return_value.sort.return_value = mock_cursor
        
        start = datetime(2026, 1, 1)
        end = datetime(2026, 1, 31)
        logs = db.get_nutrition_logs_by_date_range("test@test.com", start, end)
        
        assert len(logs) == 1
        assert isinstance(logs[0], NutritionLog)

    def test_get_by_date_range_uses_proper_boundaries(self, db):
        """Verify date range uses start of day and end of day."""
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = lambda self: iter([])
        db.nutrition.collection.find.return_value.sort.return_value = mock_cursor
        
        start = datetime(2026, 1, 10, 14, 30)  # Mid-day time
        end = datetime(2026, 1, 15, 8, 0)
        
        db.get_nutrition_logs_by_date_range("test@test.com", start, end)
        
        call_args = db.nutrition.collection.find.call_args[0][0]
        # Start should be at 00:00:00
        assert call_args["date"]["$gte"].hour == 0
        assert call_args["date"]["$gte"].minute == 0
        # End should be at 23:59:59
        assert call_args["date"]["$lte"].hour == 23
        assert call_args["date"]["$lte"].minute == 59
