import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime, timedelta
from src.api.models.weight_log import WeightLog
from src.services.database import MongoDatabase


class TestDatabaseWeight:
    @pytest.fixture
    def db(self):
        with patch("src.services.database.pymongo.MongoClient") as mock_client:
            # Setup mock database and collection
            mock_db_instance = MagicMock()
            mock_client.return_value.__getitem__.return_value = mock_db_instance

            # Create service instance
            service = MongoDatabase()

            yield service

    def test_save_weight_log_with_composition(self, db):
        """Save log with body composition fields and retrieve."""
        log = WeightLog(
            user_email="test@test.com",
            date=date.today(),
            weight_kg=76.8,
            body_fat_pct=24.2,
            muscle_mass_pct=55.2,
            bone_mass_kg=2.96,
            source="scale_import",
        )

        # Setup mock return for update_one (upsert)
        db.weight.collection.update_one.return_value.upserted_id = "new_id_123"

        doc_id, is_new = db.save_weight_log(log)
        assert is_new is True
        assert doc_id == "new_id_123"

        # Verify call args
        db.weight.collection.update_one.assert_called_once()
        call_args = db.weight.collection.update_one.call_args
        query = call_args[0][0]
        update = call_args[0][1]

        # Verify query matches
        assert query["user_email"] == "test@test.com"
        # Date should be datetime in query
        assert isinstance(query["date"], datetime)

        # Verify update data contains new fields
        set_data = update["$set"]
        assert set_data["body_fat_pct"] == 24.2
        assert set_data["muscle_mass_pct"] == 55.2

        # Verify source is stored
        assert set_data["source"] == "scale_import"

    def test_upsert_updates_composition(self, db):
        """Re-saving same date updates all fields."""
        log = WeightLog(
            user_email="x@x.com", date=date.today(), weight_kg=76.0, body_fat_pct=25.0
        )

        # Setup mock for existing record update (no upserted_id)
        db.weight.collection.update_one.return_value.upserted_id = None
        # Setup find_one to return the "updated" doc ID
        db.weight.collection.find_one.return_value = {"_id": "existing_id"}

        doc_id, is_new = db.save_weight_log(log)

        assert is_new is False
        assert doc_id == "existing_id"

        # Verify update call
        db.weight.collection.update_one.assert_called_once()
        set_data = db.weight.collection.update_one.call_args[0][1]["$set"]
        assert set_data["weight_kg"] == 76.0
        assert set_data["body_fat_pct"] == 25.0

    def test_get_by_date_range_includes_composition(self, db):
        """Date range query returns composition fields."""
        # Setup mock cursor
        mock_doc = {
            "user_email": "range@test.com",
            "date": datetime.now(),  # DB returns datetime
            "weight_kg": 78.0,
            "body_fat_pct": 26.0,
            "_id": "some_id",
        }

        # Mock find().sort() chain
        # find() returns cursor, sort() returns cursor
        mock_cursor = MagicMock()
        mock_cursor.__iter__.return_value = [mock_doc]
        db.weight.collection.find.return_value.sort.return_value = mock_cursor

        logs = db.get_weight_logs_by_date_range(
            "range@test.com", date.today() - timedelta(days=10), date.today()
        )

        assert len(logs) == 1
        assert logs[0].body_fat_pct == 26.0
        assert logs[0].weight_kg == 78.0
