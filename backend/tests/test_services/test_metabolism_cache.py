
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from src.services.metabolism_cache import MetabolismInsightCache

@pytest.fixture
def mock_db():
    db = MagicMock()
    # Mock collection
    db.db = {"ai_insight_cache": MagicMock()}
    return db

@pytest.fixture
def cache(mock_db):
    return MetabolismInsightCache(mock_db)

def test_generate_key_stability(cache):
    """Test that cache key is stable for same input but different order."""
    user = "test@test.com"
    summary = "Hardcore Trainer"
    
    stats_1 = {"tdee": 2500, "weight": 70.0, "goal": "lose", "startDate": "ignored"}
    stats_2 = {"weight": 70.0, "goal": "lose", "tdee": 2500, "startDate": "different"}
    
    key1 = cache._generate_key(user, stats_1, summary)
    key2 = cache._generate_key(user, stats_2, summary)
    
    assert key1 == key2
    
def test_generate_key_invalidation(cache):
    """Test that key changes when logic-affecting data changes."""
    user = "test@test.com"
    summary = "Hardcore Trainer"
    
    stats_base = {"tdee": 2500, "weight": 70.0}
    stats_changed = {"tdee": 2505, "weight": 70.0} # TDEE changed
    
    key1 = cache._generate_key(user, stats_base, summary)
    key2 = cache._generate_key(user, stats_changed, summary)
    
    assert key1 != key2

def test_get_valid_cache(cache):
    mock_collection = cache.collection
    
    # Setup mock return
    mock_collection.find_one.return_value = {
        "content": "Cached Insight",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }
    
    result = cache.get("u", {}, "s")
    assert result == "Cached Insight"

def test_get_expired_cache(cache):
    mock_collection = cache.collection
    
    # Setup mock return (expired)
    mock_collection.find_one.return_value = {
        "content": "Old Insight",
        "expires_at": datetime.utcnow() - timedelta(minutes=1)
    }
    
    result = cache.get("u", {}, "s")
    assert result is None
