from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from src.services.trainer import AITrainerBrain
from src.api.models.user_profile import UserProfile
from src.api.models.chat_history import ChatHistory
from src.api.models.sender import Sender

class DummyDatabase:
    def __init__(self):
        self.calls = []
        self.history_messages = []
    def increment_user_message_counts(self, user_email, new_cycle_start):
        self.calls.append((user_email, new_cycle_start))
    def get_chat_history(self, session_id, limit, offset):
        self.calls.append((session_id, limit, offset))
        return self.history_messages

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
    cycle_start=None,
    sent_today=0,
    last_date=None
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
    profile.messages_sent_today = sent_today
    profile.last_message_date = last_date
    return profile

def test_free_plan_under_limit(trainer_brain):
    profile = create_profile(plan="Free", sent_today=19, cycle_start=datetime.now())
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is False

def test_free_plan_over_limit(trainer_brain):
    # Daily limit reached
    profile = create_profile(plan="Free", sent_today=20, last_date=datetime.now().strftime("%Y-%m-%d"), cycle_start=datetime.now())
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "DAILY_LIMIT_REACHED"

def test_free_plan_trial_expired(trainer_brain):
    # Trial expired (8 days ago)
    past_8_days = datetime.now() - timedelta(days=8)
    profile = create_profile(plan="Free", cycle_start=past_8_days)
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "TRIAL_EXPIRED"

def test_basic_plan_under_limit(trainer_brain):
    now = datetime.now()
    profile = create_profile(plan="Basic", monthly=99, cycle_start=now)
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is False

def test_basic_plan_over_limit(trainer_brain):
    now = datetime.now()
    profile = create_profile(plan="Basic", monthly=100, cycle_start=now)
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "LIMITE_MENSAGENS_MES"

def test_basic_plan_cycle_reset(trainer_brain):
    past = datetime.now() - timedelta(days=31)
    # Even if they have 100/100, the cycle should reset
    profile = create_profile(plan="Basic", monthly=100, cycle_start=past)
    needs_reset = trainer_brain.check_message_limits(profile)
    assert needs_reset is True

def test_custom_limit_override(trainer_brain):
    today = datetime.now().strftime("%Y-%m-%d")
    profile = create_profile(plan="Free", sent_today=30, last_date=today, custom_limit=50) # Limit overridden -> OK
    trainer_brain.check_message_limits(profile)

    profile = create_profile(plan="Basic", monthly=200, custom_limit=300, cycle_start=datetime.now())
    trainer_brain.check_message_limits(profile)

    profile = create_profile(plan="Free", sent_today=60, last_date=today, custom_limit=50)
    with pytest.raises(HTTPException) as exc:
        trainer_brain.check_message_limits(profile)
    assert exc.value.status_code == 403
    assert exc.value.detail == "DAILY_LIMIT_REACHED"

def test_increment_counts(trainer_brain):
    trainer_brain.increment_counts("test@test.com", True)
    assert len(trainer_brain._database.calls) == 1
    assert trainer_brain._database.calls[0][0] == "test@test.com"
    assert trainer_brain._database.calls[0][1] is not None

def test_get_chat_history_normalizes_flattened_trainer_tables(trainer_brain):
    trainer_brain._database.history_messages = [
        ChatHistory(
            text="| Dia | Calorias | | :--- | :--- | | 13/04 | 1995 |",
            translations={
                "pt-BR": "\\u007c Dia \\u007c Calorias \\u007c \\u007c :--- \\u007c :--- \\u007c \\u007c 13/04 \\u007c 1995 \\u007c",
            },
            sender=Sender.TRAINER,
            timestamp="2024-01-01T10:00:00",
        )
    ]

    messages = trainer_brain.get_chat_history("test@test.com")

    assert len(messages) == 1
    assert messages[0].text == "| Dia | Calorias |\n| :--- | :--- |\n| 13/04 | 1995 |"
    assert messages[0].translations == {
        "pt-BR": "| Dia | Calorias |\n| :--- | :--- |\n| 13/04 | 1995 |"
    }
