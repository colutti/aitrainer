import pytest
from unittest.mock import MagicMock
from src.services.profile_tools import create_get_user_goal_tool, create_update_user_goal_tool
from src.api.models.user_profile import UserProfile

class TestProfileTools:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.user_email = "test@example.com"
        self.mock_profile = UserProfile(
            email=self.user_email,
            gender="Masculino",
            age=25,
            weight=80.0,
            height=180,
            goal="Legacy Goal",
            goal_type="maintain",
            weekly_rate=0.0,
            notes="Initial notes"
        )
        self.mock_db.get_user_profile.return_value = self.mock_profile

    def test_get_user_goal(self):
        tool = create_get_user_goal_tool(self.mock_db, self.user_email)
        result = tool.run({})
        
        assert "Tipo de Objetivo | Manter peso" in result
        assert "Taxa Semanal | 0.0kg/semana" in result
        assert "Observações | Initial notes" in result

    def test_update_user_goal_success(self):
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        result = tool.run({"goal_type": "lose", "weekly_rate": 0.5})
        
        assert "Perfil atualizado com sucesso!" in result
        assert "focado em perda de peso com uma taxa de 0.5kg/semana" in result
        
        # Verify DB calls
        self.mock_db.save_user_profile.assert_called_once()
        updated_profile = self.mock_db.save_user_profile.call_args[0][0]
        assert updated_profile.goal_type == "lose"
        assert updated_profile.weekly_rate == 0.5

    def test_update_user_goal_invalid_type(self):
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        result = tool.run({"goal_type": "invalid", "weekly_rate": 0.5})
        assert "Erro: goal_type deve ser" in result

    def test_update_user_goal_missing_rate(self):
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        # For lose, weekly_rate is required
        result = tool.run({"goal_type": "lose"})
        assert "Erro: weekly_rate (taxa semanal) é obrigatório" in result

    def test_update_user_goal_maintain_resets_rate(self):
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        result = tool.run({"goal_type": "maintain"})
        
        assert "focado em manutenção" in result
        updated_profile = self.mock_db.save_user_profile.call_args[0][0]
        assert updated_profile.goal_type == "maintain"
        assert updated_profile.weekly_rate == 0.0
