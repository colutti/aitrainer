import pytest
from datetime import datetime
from unittest.mock import MagicMock
from src.services.myfitnesspal_import_service import parse_csv_content, import_nutrition_from_csv, DailyNutrition
from src.api.models.nutrition_log import NutritionLog

CSV_CONTENT_VALID = """Data,Refeição,Calorias,Gorduras (g),Carboidratos (g),Proteínas (g)
2024-01-01,Café da Manhã,300,10,30,20
2024-01-01,Almoço,600,20,50,40
2024-01-02,Jantar,500,15,40,30
"""

CSV_CONTENT_INVALID = """Data,Refeição,Calorias
2024-01-01,Café da Manhã,300
"""

class TestMyFitnessPalImport:

    def test_parse_csv_content_valid(self):
        """Test parsing valid CSV content."""
        result = parse_csv_content(CSV_CONTENT_VALID)
        
        assert len(result) == 2
        assert "2024-01-01" in result
        assert "2024-01-02" in result
        
        day1 = result["2024-01-01"]
        assert day1.calories == 900.0  # 300 + 600
        assert day1.protein == 60.0    # 20 + 40
        assert len(day1.meals) == 2

    def test_parse_csv_content_invalid_columns(self):
        """Test that missing columns raise ValueError."""
        with pytest.raises(ValueError) as exc:
            parse_csv_content(CSV_CONTENT_INVALID)
        assert "Colunas obrigatórias ausentes" in str(exc.value)

    def test_import_process_db_calls(self):
        """Test the full import process with mock DB."""
        mock_db = MagicMock()
        mock_db.save_nutrition_log.return_value = ("id123", True)
        
        user_email = "test@user.com"
        result = import_nutrition_from_csv(user_email, CSV_CONTENT_VALID, mock_db)
        
        assert result.total_days == 2
        assert result.created == 2
        assert result.updated == 0
        assert result.errors == 0
        
        # Verify DB was called correctly
        assert mock_db.save_nutrition_log.call_count == 2
        
        # Check first call arg
        call_args = mock_db.save_nutrition_log.call_args_list
        log1 = call_args[0][0][0] # First call, first arg
        # Since we sort by date, 2024-01-01 comes first
        assert isinstance(log1, NutritionLog)
        assert log1.user_email == user_email
        assert log1.calories == 900
        assert log1.source == "myfitnesspal"

    def test_import_updates(self):
        """Test that existing logs count as updates."""
        mock_db = MagicMock()
        # First call new, Second call update
        mock_db.save_nutrition_log.side_effect = [("id1", True), ("id2", False)]
        
        result = import_nutrition_from_csv("u", CSV_CONTENT_VALID, mock_db)
        
        assert result.created == 1
        assert result.updated == 1

    def test_import_db_error(self):
        """Test handling of DB errors during save."""
        mock_db = MagicMock()
        mock_db.save_nutrition_log.side_effect = Exception("DB Bomb")
        
        result = import_nutrition_from_csv("u", CSV_CONTENT_VALID, mock_db)
        
        assert result.errors == 2
        assert len(result.error_messages) == 2
        assert "DB Bomb" in result.error_messages[0]
