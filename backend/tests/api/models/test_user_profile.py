from src.api.models.user_profile import UserProfile


def test_user_profile_has_subscription_fields():
    profile = UserProfile(gender="Masculino", age=30, height=180, goal_type="maintain", email="test@example.com")
    assert hasattr(profile, "messages_sent_today")
    assert hasattr(profile, "last_message_date")
    assert profile.messages_sent_today == 0
    assert profile.last_message_date is None

def test_user_profile_accepts_subscription_fields():
    profile = UserProfile(
        gender="Masculino", 
        age=30, 
        height=180, 
        goal_type="maintain", 
        email="test@example.com", 
        messages_sent_today=5,
        last_message_date="2026-03-08"
    )
    assert profile.messages_sent_today == 5
    assert profile.last_message_date == "2026-03-08"


def test_user_profile_summary_omits_legacy_goal_and_weight_fields():
    profile = UserProfile(
        gender="Masculino",
        age=30,
        height=180,
        goal_type="lose",
        weekly_rate=0.5,
        weight=78.0,
        email="test@example.com",
        display_name="Atleta Teste",
        notes="Sem restrições",
    )

    summary = profile.get_profile_summary()

    assert "**Peso Inicial:**" not in summary
    assert "**Tipo de Objetivo:**" not in summary
    assert "**Taxa Semanal:**" not in summary
    assert "**Nome:** Atleta Teste" in summary
    assert "**Observações:** Sem restrições" in summary
