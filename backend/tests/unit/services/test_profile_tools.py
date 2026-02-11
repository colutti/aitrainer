
import unittest
from unittest.mock import MagicMock
from src.services.profile_tools import create_get_user_goal_tool, create_update_user_goal_tool
from src.api.models.user_profile import UserProfile

class TestProfileTools(unittest.TestCase):
    def setUp(self):
        self.mock_db = MagicMock()
        self.user_email = "test@example.com"
        
        # Setup common mock profile
        self.mock_profile = MagicMock(spec=UserProfile)
        self.mock_profile.goal_type = "maintain"
        self.mock_profile.weekly_rate = 0.0
        self.mock_profile.email = self.user_email
        self.mock_profile.get_profile_summary.return_value = "Summary: Maintain"
        
        self.mock_db.get_user_profile.return_value = self.mock_profile

    def test_get_goal_success(self):
        """Test getting user goal successfully."""
        tool = create_get_user_goal_tool(self.mock_db, self.user_email)
        
        result = tool.invoke({})
        
        self.assertIn("objetivo atual do aluno", result)
        self.assertIn("Summary: Maintain", result)
        self.mock_db.get_user_profile.assert_called_with(self.user_email)

    def test_get_goal_not_found(self):
        """Test getting goal when profile not found."""
        tool = create_get_user_goal_tool(self.mock_db, self.user_email)
        self.mock_db.get_user_profile.return_value = None
        
        result = tool.invoke({})
        
        self.assertIn("Perfil do aluno não encontrado", result)

    def test_update_goal_success_lose(self):
        """Test updating goal to lose weight."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        
        result = tool.invoke({"goal_type": "lose", "weekly_rate": 0.5})
        
        self.assertIn("atualizado com sucesso", result)
        self.assertIn("perda de peso", result)
        self.assertIn("0.5kg/semana", result)
        
        # Verify profile updates
        self.assertEqual(self.mock_profile.goal_type, "lose")
        self.assertEqual(self.mock_profile.weekly_rate, 0.5)
        self.mock_db.save_user_profile.assert_called_once_with(self.mock_profile)

    def test_update_goal_success_maintain(self):
        """Test updating goal to maintain (should auto-set rate to 0)."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        
        # Start with non-zero
        self.mock_profile.weekly_rate = 0.5
        
        result = tool.invoke({"goal_type": "maintain"})
        
        self.assertIn("atualizado com sucesso", result)
        self.assertIn("manutenção", result)
        
        self.assertEqual(self.mock_profile.goal_type, "maintain")
        self.assertEqual(self.mock_profile.weekly_rate, 0.0)
        self.mock_db.save_user_profile.assert_called_once()

    def test_update_goal_invalid_type(self):
        """Test updating with invalid goal type."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        
        result = tool.invoke({"goal_type": "fly", "weekly_rate": 0.5})
        
        self.assertIn("deve ser 'lose', 'gain' ou 'maintain'", result)
        self.mock_db.save_user_profile.assert_not_called()

    def test_update_goal_missing_rate(self):
        """Test updating lose/gain without rate."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        
        # Case 1: None
        result = tool.invoke({"goal_type": "lose"})
        self.assertIn("taxa semanal", result)
        
        # Case 2: Zero
        result = tool.invoke({"goal_type": "gain", "weekly_rate": 0.0})
        self.assertIn("taxa semanal", result)
        
        self.mock_db.save_user_profile.assert_not_called()

    def test_update_goal_profile_not_found(self):
        """Test updating when profile not found."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        self.mock_db.get_user_profile.return_value = None
        
        result = tool.invoke({"goal_type": "maintain"})
        
        self.assertIn("Perfil do aluno não encontrado", result)

    def test_update_goal_exception(self):
        """Test exception handling during update."""
        tool = create_update_user_goal_tool(self.mock_db, self.user_email)
        self.mock_db.save_user_profile.side_effect = Exception("DB Error")
        
        result = tool.invoke({"goal_type": "maintain"})
        
        self.assertIn("Erro ao atualizar perfil", result)
