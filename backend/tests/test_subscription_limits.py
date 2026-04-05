from datetime import datetime, timedelta, timezone
import pytest
from fastapi import HTTPException
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile

class DummyDatabase:
    def __init__(self):
        self.calls = []
    def increment_user_message_counts(self, user_email, new_cycle_start, photo_count=0):
        self.calls.append((user_email, new_cycle_start, photo_count))

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
    photos=0,
    total=0,
    cycle_start=None,
    trial_ends_at=None,
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
    profile.photos_sent_this_month = photos
    profile.total_messages_sent = total
    profile.current_billing_cycle_start = cycle_start
    profile.trial_ends_at = trial_ends_at
    return profile

def test_free_active_trial_under_limit(trainer_brain):
    profile = create_profile(
        plan="Free",
        monthly=10,
        cycle_start=datetime.now(timezone.utc),
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is False


def test_free_trial_over_monthly_limit(trainer_brain):
    profile = create_profile(
        plan="Free",
        monthly=500,
        cycle_start=datetime.now(timezone.utc),
        trial_ends_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_MES"


def test_free_plan_trial_expired_blocks_chat(trainer_brain):
    profile = create_profile(
        plan="Free",
        cycle_start=datetime.now(timezone.utc),
        trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "CHAT_NOT_ALLOWED_FOR_PLAN"


def test_pro_plan_under_limit(trainer_brain):
    now = datetime.now(timezone.utc)
    profile = create_profile(plan="Pro", monthly=499, cycle_start=now)
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is False


def test_pro_plan_over_limit(trainer_brain):
    now = datetime.now(timezone.utc)
    profile = create_profile(plan="Pro", monthly=500, cycle_start=now)
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_MES"


def test_pro_plan_cycle_reset(trainer_brain):
    past = datetime.now(timezone.utc) - timedelta(days=31)
    profile = create_profile(plan="Pro", monthly=500, photos=15, cycle_start=past)
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is True


def test_photo_limit_for_pro(trainer_brain):
    profile = create_profile(
        plan="Pro",
        photos=14,
        cycle_start=datetime.now(timezone.utc),
    )
    trainer_brain.check_image_limit(profile, 1)
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_image_limit(profile, 2)
    assert exc.value.status_code == 403
    assert exc.value.detail == "PHOTO_LIMIT_REACHED"


def test_custom_limit_override(trainer_brain):
    profile = create_profile(
        plan="Pro",
        monthly=250,
        custom_limit=300,
        cycle_start=datetime.now(timezone.utc),
    )
    trainer_brain.check_message_limits(profile)

    profile = create_profile(
        plan="Pro",
        monthly=350,
        custom_limit=300,
        cycle_start=datetime.now(timezone.utc),
    )
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_MES"

def test_increment_counts(trainer_brain):
    trainer_brain.increment_counts("test@test.com", True, 2)
    assert len(trainer_brain._database.calls) == 1
    assert trainer_brain._database.calls[0][0] == "test@test.com"
    assert trainer_brain._database.calls[0][1] is not None
    assert trainer_brain._database.calls[0][2] == 2
