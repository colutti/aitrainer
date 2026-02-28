from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.core.subscription import SubscriptionPlan

class DummyDatabase:
    def __init__(self):
        self.calls = []
    def increment_user_message_counts(self, user_email, new_cycle_start):
        self.calls.append((user_email, new_cycle_start))

class DummyTrainerBrain(AITrainerBrain):
    def __init__(self):
        self._database = DummyDatabase()

@pytest.fixture
def trainer_brain():
    return DummyTrainerBrain()

def create_profile(
    plan="Free", 
    custom_limit=None, 
    monthly=0, 
    total=0,
    cycle_start=None
):
    profile = UserProfile(
        email="test@test.com",
        gender="Masculino",
        age=30,
        height=180,
        weight=80,
        goal_type="maintain",
        weekly_rate=0.5,
    )
    profile.subscription_plan = plan
    profile.custom_message_limit = custom_limit
    profile.messages_sent_this_month = monthly
    profile.total_messages_sent = total
    profile.current_billing_cycle_start = cycle_start
    return profile

def test_free_plan_under_limit(trainer_brain):
    profile = create_profile(plan="Free", total=19)
    needs_reset = trainer_brain._check_message_limits(profile)
    assert needs_reset is True # Since cycle_start is None

def test_free_plan_over_limit(trainer_brain):
    profile = create_profile(plan="Free", total=20)
    with pytest.raises(HTTPException) as exc:
        trainer_brain._check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_TOTAL"

def test_basic_plan_under_limit(trainer_brain):
    now = datetime.now()
    profile = create_profile(plan="Basic", monthly=99, cycle_start=now)
    needs_reset = trainer_brain._check_message_limits(profile)
    assert needs_reset is False

def test_basic_plan_over_limit(trainer_brain):
    now = datetime.now()
    profile = create_profile(plan="Basic", monthly=100, cycle_start=now)
    with pytest.raises(HTTPException) as exc:
        trainer_brain._check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_MES"

def test_basic_plan_cycle_reset(trainer_brain):
    past = datetime.now() - timedelta(days=31)
    # Even if they have 100/100, the cycle should reset
    profile = create_profile(plan="Basic", monthly=100, cycle_start=past)
    needs_reset = trainer_brain._check_message_limits(profile)
    assert needs_reset is True

def test_custom_limit_override(trainer_brain):
    profile = create_profile(plan="Free", total=30, custom_limit=50) # Limit overridden -> OK
    trainer_brain._check_message_limits(profile)

    profile = create_profile(plan="Basic", monthly=200, custom_limit=300, cycle_start=datetime.now())
    trainer_brain._check_message_limits(profile)

    profile = create_profile(plan="Free", total=60, custom_limit=50)
    with pytest.raises(HTTPException):
        trainer_brain._check_message_limits(profile)

def test_increment_counts(trainer_brain):
    trainer_brain._increment_counts("test@test.com", True)
    assert len(trainer_brain._database.calls) == 1
    assert trainer_brain._database.calls[0][0] == "test@test.com"
    assert trainer_brain._database.calls[0][1] is not None
