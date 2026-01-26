import pytest
from unittest.mock import MagicMock
from datetime import date, datetime, timedelta, timezone
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
        NutritionLog(
            user_email="u",
            date=datetime.now(),
            calories=2000,
            protein_grams=150,
            carbs_grams=200,
            fat_grams=60,
        )
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
    w_logs_2 = w_logs + [
        WeightLog(user_email="u", date=date.today(), weight_kg=71.0, source="manual")
    ]
    key2 = cache._generate_key(user, w_logs_2, n_logs, user_goal, trainer_type)
    assert key1 != key2

    # Change goal
    user_goal_changed = {"goal_type": "gain", "weekly_rate": 0.5}
    key3 = cache._generate_key(user, w_logs, n_logs, user_goal_changed, trainer_type)
    assert key1 != key3


def test_cache_invalidates_on_target_weight_change(cache):
    """Test that cache invalidates when target_weight changes."""
    user = "test@test.com"
    trainer_type = "atlas"
    w_logs, n_logs = mock_logs()

    user_goal_1 = {"goal_type": "lose", "weekly_rate": 0.5, "target_weight": 75}
    user_goal_2 = {"goal_type": "lose", "weekly_rate": 0.5, "target_weight": 70}

    key1 = cache._generate_key(user, w_logs, n_logs, user_goal_1, trainer_type)
    key2 = cache._generate_key(user, w_logs, n_logs, user_goal_2, trainer_type)

    assert key1 != key2, "Cache should invalidate when target_weight changes"


def test_cache_invalidates_on_historical_edit(cache):
    """Test that cache invalidates when first (oldest) log is edited."""
    user = "test@test.com"
    trainer_type = "atlas"
    user_goal = {"goal_type": "lose", "weekly_rate": 0.5}

    # Create multiple logs
    today = date.today()
    w_logs = [
        WeightLog(user_email="u", date=today - timedelta(days=10), weight_kg=80.0, source="manual"),
        WeightLog(user_email="u", date=today - timedelta(days=5), weight_kg=79.0, source="manual"),
        WeightLog(user_email="u", date=today, weight_kg=78.0, source="manual"),
    ]
    n_logs = []

    key1 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)

    # Edit first (oldest) log - change date
    w_logs_edited = [
        WeightLog(user_email="u", date=today - timedelta(days=11), weight_kg=80.0, source="manual"),
        WeightLog(user_email="u", date=today - timedelta(days=5), weight_kg=79.0, source="manual"),
        WeightLog(user_email="u", date=today, weight_kg=78.0, source="manual"),
    ]

    key2 = cache._generate_key(user, w_logs_edited, n_logs, user_goal, trainer_type)

    assert key1 != key2, "Cache should invalidate when historical data is edited"


def test_cache_stable_when_nothing_changes(cache):
    """Test that cache remains valid when no data changes."""
    user = "test@test.com"
    trainer_type = "atlas"
    user_goal = {"goal_type": "lose", "weekly_rate": 0.5, "target_weight": 75}
    w_logs, n_logs = mock_logs()

    key1 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)
    key2 = cache._generate_key(user, w_logs, n_logs, user_goal, trainer_type)

    assert key1 == key2, "Cache should remain valid when nothing changes"


def test_cache_handles_none_target_weight(cache):
    """Test that cache handles None target_weight gracefully."""
    user = "test@test.com"
    trainer_type = "atlas"
    w_logs, n_logs = mock_logs()

    user_goal_1 = {"goal_type": "lose", "weekly_rate": 0.5, "target_weight": None}
    user_goal_2 = {"goal_type": "lose", "weekly_rate": 0.5, "target_weight": 0}

    # Both None and 0 should be treated the same (as 0)
    key1 = cache._generate_key(user, w_logs, n_logs, user_goal_1, trainer_type)
    key2 = cache._generate_key(user, w_logs, n_logs, user_goal_2, trainer_type)

    assert key1 == key2, "None and 0 target_weight should produce same cache key"




def test_get_valid_cache(cache):
    mock_collection = cache.collection
    w_logs, n_logs = mock_logs()

    # Setup mock return
    mock_collection.find_one.return_value = {
        "content": "Cached Insight",
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }

    result = cache.get("u", w_logs, n_logs, {}, "atlas")
    assert result == "Cached Insight"


def test_get_expired_cache(cache):
    mock_collection = cache.collection
    w_logs, n_logs = mock_logs()

    # Setup mock return (expired)
    mock_collection.find_one.return_value = {
        "content": "Old Insight",
        "expires_at": datetime.now(timezone.utc) - timedelta(minutes=1),
    }

    result = cache.get("u", w_logs, n_logs, {}, "atlas")
    assert result is None
