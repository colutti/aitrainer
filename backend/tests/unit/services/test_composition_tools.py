"""
Tests for body composition tracking tools.
"""

import pytest
from unittest.mock import MagicMock
from datetime import date

from src.services.composition_tools import (
    create_save_composition_tool,
    create_get_composition_tool,
)
from src.api.models.weight_log import WeightLog


class TestCompositionTools:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_save_body_composition_creates_new(self, mock_db):
        """Test creating a new body composition log."""
        # Setup
        mock_db.save_weight_log.return_value = ("new_id_123", True)
        tool = create_save_composition_tool(mock_db, "user@test.com")

        # Execute
        result = tool.invoke(
            {
                "weight_kg": 80.5,
                "body_fat_pct": 15.2,
                "muscle_mass_pct": 40.0,
                "date": "2024-01-01",
            }
        )

        # Verify
        mock_db.save_weight_log.assert_called_once()
        args = mock_db.save_weight_log.call_args[0][0]
        assert isinstance(args, WeightLog)
        assert args.weight_kg == 80.5
        assert args.body_fat_pct == 15.2
        assert args.user_email == "user@test.com"
        assert args.date == date(2024, 1, 1)

        assert "registrada com sucesso" in result
        assert "ID: new_id_123" in result

    def test_save_body_composition_updates_existing(self, mock_db):
        """Test updating an existing body composition log (upsert)."""
        # Setup
        mock_db.save_weight_log.return_value = ("existing_id_456", False)
        tool = create_save_composition_tool(mock_db, "user@test.com")

        # Execute
        result = tool.invoke({"weight_kg": 81.0, "notes": "Pesagem pós-treino"})

        # Verify
        mock_db.save_weight_log.assert_called_once()
        assert "atualizada com sucesso" in result
        assert "ID: existing_id_456" in result

    def test_save_body_composition_error_handling(self, mock_db):
        """Test error handling during save."""
        mock_db.save_weight_log.side_effect = Exception("DB Error")
        tool = create_save_composition_tool(mock_db, "user@test.com")

        result = tool.invoke({"weight_kg": 80.0})

        assert "Erro ao salvar composição corporal" in result

    def test_get_body_composition_empty(self, mock_db):
        """Test getting composition when no logs exist."""
        mock_db.get_weight_logs.return_value = []
        tool = create_get_composition_tool(mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        assert "Nenhum registro de composição corporal" in result

    def test_get_body_composition_success(self, mock_db):
        """Test getting composition logs successfully."""
        mock_db.get_weight_logs.return_value = [
            WeightLog(
                user_email="user@test.com",
                date=date(2024, 1, 1),
                weight_kg=80.0,
                body_fat_pct=15.0,
                muscle_mass_pct=42.0,
                bmr=1850,
            )
        ]
        tool = create_get_composition_tool(mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        assert "Encontrei 1 registro" in result
        assert (
            "01/01/2024: Peso: 80.0kg, Gordura: 15.0%, Músculo: 42.0%, BMR: 1850 kcal"
            in result
        )

    def test_save_body_composition_with_measurements(self, mock_db):
        """Test saving body composition with circumference measurements."""
        # Setup
        mock_db.save_weight_log.return_value = ("meas_id_789", True)
        tool = create_save_composition_tool(mock_db, "user@test.com")

        # Execute
        result = tool.invoke(
            {
                "weight_kg": 75.0,
                "waist_cm": 80.5,
                "hips_cm": 95.0,
                "chest_cm": 98.0,
                "neck_cm": 37.5,
                "bicep_r_cm": 32.0,
                "bicep_l_cm": 31.5,
                "thigh_r_cm": 52.0,
                "thigh_l_cm": 51.5,
            }
        )

        # Verify
        mock_db.save_weight_log.assert_called_once()
        args = mock_db.save_weight_log.call_args[0][0]
        assert args.waist_cm == 80.5
        assert args.hips_cm == 95.0
        assert args.chest_cm == 98.0
        assert args.neck_cm == 37.5
        assert args.bicep_r_cm == 32.0
        assert args.bicep_l_cm == 31.5
        assert "registrada com sucesso" in result

    def test_get_body_composition_with_measurements(self, mock_db):
        """Test getting composition logs with circumference measurements."""
        mock_db.get_weight_logs.return_value = [
            WeightLog(
                user_email="user@test.com",
                date=date(2024, 1, 15),
                weight_kg=75.0,
                body_fat_pct=18.0,
                waist_cm=80.5,
                hips_cm=95.0,
                chest_cm=98.0,
                neck_cm=37.5,
                bicep_r_cm=32.0,
                bicep_l_cm=31.5,
                thigh_r_cm=52.0,
                thigh_l_cm=51.5,
            )
        ]
        tool = create_get_composition_tool(mock_db, "user@test.com")

        result = tool.invoke({"limit": 5})

        assert "Encontrei 1 registro" in result
        assert "Medidas: Pescoço: 37.5cm, Peito: 98.0cm, Cintura: 80.5cm" in result
        assert "Quadril: 95.0cm" in result
        assert "Bíceps: D=32.0cm E=31.5cm" in result
        assert "Coxa: D=52.0cm E=51.5cm" in result
