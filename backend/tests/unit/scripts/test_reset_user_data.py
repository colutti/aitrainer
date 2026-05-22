from scripts.reset_user_data import MONGO_COLLECTIONS


def test_reset_user_data_clears_plan_discovery_state():
    assert ("plan_discovery_states", "user_email") in MONGO_COLLECTIONS
