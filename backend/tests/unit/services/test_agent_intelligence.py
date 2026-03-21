from unittest.mock import MagicMock, patch
from src.services.nutrition_tools import create_sync_nutrition_text_tool
from src.services.metabolism_tools import create_get_metabolism_tool
from src.services.trainer import AITrainerBrain
from langchain_core.messages import AIMessage, HumanMessage

def test_sync_nutrition_text_tool():
    mock_db = MagicMock()
    mock_db.save_nutrition_log.return_value = ("doc_id", True)
    
    tool = create_sync_nutrition_text_tool(mock_db, "user@test.com")
    
    text = """
19 de mar. de 2026
TOTAIS 1748 153 47 182
    """
    result = tool.invoke({"raw_text": text})
    
    assert "Sincronização concluída" in result
    assert "19/03/2026 (criado)" in result
    assert mock_db.save_nutrition_log.called

@patch("src.services.metabolism_tools.AdaptiveTDEEService")
def test_get_metabolism_data_raw(mock_tdee_service_class):
    mock_db = MagicMock()
    mock_service = mock_tdee_service_class.return_value
    mock_service.calculate_tdee.return_value = {
        "tdee": 2500,
        "daily_target": 2000,
        "goal_type": "lose",
        "goal_weekly_rate": 0.5,
        "weight_trend": [
            {"date": "2026-03-19", "weight": 72.8, "trend": 73.0},
            {"date": "2026-03-18", "weight": 72.9, "trend": 73.1},
            {"date": "2026-03-17", "weight": 72.7, "trend": 73.2},
        ],
        "calorie_trend": [
            {"date": "2026-03-19", "calories": 1800},
            {"date": "2026-03-18", "calories": 1750},
        ]
    }
    mock_db.get_user_profile.return_value = MagicMock(tdee_activity_factor=1.55, tdee_last_check_in="2026-03-15")
    
    tool = create_get_metabolism_tool(mock_db, "user@test.com")
    result = tool.invoke({})
    
    assert "=== METABOLISMO: DADOS BRUTOS" in result
    assert "AUDITORIA DE LOWS" in result
    assert "2026-03-19: Peso  72.8 kg | Cal  1800 kcal" in result
    assert "Fator Atividade (Âncora): 1.55" in result
    assert "COMO O SISTEMA V4 DE TDEE FUNCIONA" in result

def test_trainer_history_prefixing():
    mock_db = MagicMock()
    mock_llm = MagicMock()
    brain = AITrainerBrain(mock_db, mock_llm)
    
    messages = [
        HumanMessage(content="Hi", additional_kwargs={"timestamp": "2026-03-20T09:59:00"}),
        AIMessage(content="Hello", additional_kwargs={"trainer_type": "atlas", "timestamp": "2026-03-20T10:00:00"}),
        AIMessage(content="Yo", additional_kwargs={"trainer_type": "gymbro", "timestamp": "2026-03-20T10:01:00"})
    ]
    
    formatted = brain.format_history_as_messages(messages)
    
    # Check prefixes
    assert '<treinador name="Atlas">Hello</treinador>' in formatted[1].content
    assert '<treinador name="Gymbro">Yo</treinador>' in formatted[2].content
    # Check XML tags
    assert '<msg data="20/03" hora="10:00">' in formatted[1].content
    assert "</msg>" in formatted[1].content
