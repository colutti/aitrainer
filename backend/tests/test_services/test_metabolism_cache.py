
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, date
from src.services.metabolism_cache import MetabolismInsightCache
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock collection
    db.database = {"ai_insight_cache": MagicMock()}
    return db

@pytest.fixture
def cache(mock_db):
    return MetabolismInsightCache(mock_db)

def mock_logs():
    w_logs = [
        WeightLog(user_email="u", date=date.today(), weight_kg=70.0, source="manual")
    ]
    n_logs = [
        NutritionLog(user_email="u", date=datetime.now(), calories=2000, protein_grams=150, carbs_grams=200, fat_grams=60)
    ]
    return w_logs, n_logs

def test_generate_key_stability(cache):
    """Test that cache key is stable for same input."""
    user = "test@test.com"
    trainer_type = "atlas"
    user_goal = {"goal_type": "lose", "weekly_rate": 0.5}
    
    w_logs, n_logs = mock_logs()
    
    # Needs to patch datetime to ensure hourly stability during test
    # but for now we assume test runs fast enough within same hour or just check format
    
    key1 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)
    key2 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)
    
    assert key1 == key2
    
def test_generate_key_invalidation(cache):
    """Test that key changes when logic-affecting data changes."""
    user = "test@test.com"
    trainer_type = "atlas"
    user_goal = {"goal_type": "lose", "weekly_rate": 0.5}
    
    w_logs, n_logs = mock_logs()
    
    key1 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)
    
    # Change weight log count
    w_logs_2 = w_logs + [WeightLog(user_email="u", date=date.today(), weight_kg=71.0, source="manual")]
    key2 = cache._generate_key(user, w_logs_2, n_logs, user_goal, trainer_type)
    assert key1 != key2
    
    # Change goal
    user_goal_changed = {"goal_type": "gain", "weekly_rate": 0.5}
    key3 = cache._generate_key(user, w_logs, n_logs, user_goal_changed, trainer_type)
    assert key1 != key3

def test_get_valid_cache(cache):
    mock_collection = cache.collection
    w_logs, n_logs = mock_logs()
    
    # Setup mock return
    mock_collection.find_one.return_value = {
        "content": "Cached Insight",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    result = cache.get("u", w_logs, n_logs, {}, "atlas")
    assert result == "Cached Insight"

def test_get_expired_cache(cache):
    mock_collection = cache.collection
    w_logs, n_logs = mock_logs()
    
    # Setup mock return (expired)
    mock_collection.find_one.return_value = {
        "content": "Old Insight",
        "expires_at": datetime.utcnow() - timedelta(minutes=1)
    }
    
    result = cache.get("u", w_logs, n_logs, {}, "atlas")
    assert result is None
