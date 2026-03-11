"""Tests for metabolism tools (TDEE reading and parameter adjustment)."""
from unittest.mock import MagicMock, patch
from src.services.metabolism_tools import (
    create_get_metabolism_tool,
    create_update_tdee_params_tool,
)
from src.api.models.user_profile import UserProfile


def test_get_metabolism_tool_returns_tdee_data():
    """Test that get_metabolism_tool returns TDEE data with algorithm explanation."""
    mock_db = MagicMock()

    with patch("src.services.metabolism_tools.AdaptiveTDEEService") as mock_tdee_service_class:
        mock_tdee_service = MagicMock()
        mock_tdee_service_class.return_value = mock_tdee_service

        mock_tdee_service.calculate_tdee.return_value = {
            "tdee": 1850,
            "daily_target": 1500,
            "confidence": "medium",
            "confidence_reason": "Partial adherence",
            "weight_logs_count": 18,
            "energy_balance": -350,
            "status": "deficit",
            "goal_type": "lose",
            "goal_weekly_rate": 0.5,
        }

        mock_profile = UserProfile(
            email="test@example.com",
            gender="Masculino",
            age=30,
            height=175,
            goal_type="maintain",
            tdee_activity_factor=1.45,
        )
        mock_db.get_user_profile.return_value = mock_profile

        tool = create_get_metabolism_tool(mock_db, "test@example.com")
        result = tool.invoke({})

        assert "TDEE atual" in result or "tdee" in result.lower()
        assert "1850" in result
        assert "1500" in result
        assert "COMO ESTE TDEE É CALCULADO" in result or "algoritmo" in result.lower()
        assert "MacroFactor" in result or "algoritmo" in result.lower()


def test_update_tdee_params_accepts_valid_activity_factor():
    """Test that update_tdee_params accepts values between 1.2 and 1.9."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")

    for factor in [1.2, 1.375, 1.55, 1.725, 1.9]:
        result = tool.invoke({"activity_factor": factor})
        assert "sucesso" in result.lower() or "updated" in result.lower()


def test_update_tdee_params_rejects_invalid_activity_factor():
    """Test that update_tdee_params rejects values outside 1.2-1.9."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")

    for factor in [1.0, 1.19, 1.91, 2.0]:
        result = tool.invoke({"activity_factor": factor})
        assert "erro" in result.lower() or "inválido" in result.lower()


def test_update_tdee_params_persists_to_database():
    """Test that update_tdee_params saves the new factor to the profile."""
    mock_db = MagicMock()
    mock_profile = UserProfile(
        email="test@example.com",
        gender="Masculino",
        age=30,
        height=175,
        goal_type="maintain",
        tdee_activity_factor=1.45,
    )
    mock_db.get_user_profile.return_value = mock_profile

    tool = create_update_tdee_params_tool(mock_db, "test@example.com")
    tool.invoke({"activity_factor": 1.2})

    mock_db.save_user_profile.assert_called_once()
    saved_profile = mock_db.save_user_profile.call_args[0][0]
    assert saved_profile.tdee_activity_factor == 1.2
