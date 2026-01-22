"""
Tests for nutrition tracking tools.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from src.services.nutrition_tools import (
    create_save_nutrition_tool,
    create_get_nutrition_tool,
)
from src.api.models.nutrition_log import NutritionLog


class TestNutritionTools:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_save_daily_nutrition_creates_new(self, mock_db):
        """Test creating a new nutrition log."""
        # Setup
        mock_db.save_nutrition_log.return_value = ("new_id_123", True)
        tool = create_save_nutrition_tool(mock_db, "user@test.com")

        # Execute
        result = tool.invoke(
            {
                "calories": 2000,
                "protein_grams": 150,
                "carbs_grams": 200,
                "fat_grams": 60,
                "date": "2024-01-01",
            }
        )

        # Verify
        mock_db.save_nutrition_log.assert_called_once()
        args = mock_db.save_nutrition_log.call_args[0][0]
        assert isinstance(args, NutritionLog)
        assert args.calories == 2000
        assert args.user_email == "user@test.com"
        assert args.date == datetime(2024, 1, 1)

        assert "criado com sucesso" in result
        assert "ID: new_id_123" in result

    def test_save_daily_nutrition_updates_existing(self, mock_db):
        """Test updating an existing nutrition log (upsert)."""
        # Setup
        mock_db.save_nutrition_log.return_value = ("existing_id_456", False)
        tool = create_save_nutrition_tool(mock_db, "user@test.com")

        # Execute
        result = tool.invoke(
            {
                "calories": 2500,
                "protein_grams": 180,
                "carbs_grams": 250,
                "fat_grams": 80,
            }
        )

        # Verify
        mock_db.save_nutrition_log.assert_called_once()
        assert "atualizado com sucesso" in result
        assert "ID: existing_id_456" in result

    def test_save_daily_nutrition_error_handling(self, mock_db):
        """Test error handling during save."""
        mock_db.save_nutrition_log.side_effect = Exception("DB Error")
        tool = create_save_nutrition_tool(mock_db, "user@test.com")

        result = tool.invoke(
            {
                "calories": 2000,
                "protein_grams": 150,
                "carbs_grams": 200,
                "fat_grams": 60,
            }
        )

        assert "Erro ao salvar log nutricional" in result

    def test_get_nutrition_empty(self, mock_db):
        """Test getting nutrition when no logs exist."""
        mock_db.get_nutrition_logs.return_value = []
        tool = create_get_nutrition_tool(mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        assert "Nenhum registro nutricional" in result

    def test_get_nutrition_success(self, mock_db):
        """Test getting nutrition logs successfully."""
        mock_db.get_nutrition_logs.return_value = [
            NutritionLog(
                user_email="test@user.com",
                date=datetime(2024, 1, 1),
                calories=2000,
                protein_grams=150,
                carbs_grams=200,
                fat_grams=60,
                fiber_grams=30,
            )
        ]
        tool = create_get_nutrition_tool(mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        assert "Encontrei 1 registro" in result
        assert "01/01/2024: 2000 kcal" in result
        assert "P: 150.0g | C: 200.0g | G: 60.0g" in result
        assert "Fibras: 30.0g" in result
