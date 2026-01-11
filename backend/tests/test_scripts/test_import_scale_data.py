import pytest
import tempfile
from pathlib import Path
from scripts.import_scale_data import parse_scale_csv

class TestImportScaleData:
    def test_parse_valid_csv(self, tmp_path):
        """Parse valid CSV with all fields."""
        csv_content = """time,weight,height,bmi,fatRate,bodyWaterRate,boneMass,metabolism,muscleRate,visceralFat
2025-12-09 06:06:59+0000,77.7,175.0,25.3,24.88,51.53,2.97,1505.0,55.4,13.0"""
        csv_file = tmp_path / "body.csv"
        csv_file.write_text(csv_content)
        
        result = parse_scale_csv(str(csv_file))
        assert "2025-12-09" in result
        data = result["2025-12-09"]
        assert data["weight_kg"] == 77.7
        assert data["body_fat_pct"] == 24.88
        assert data["bmr"] == 1505
        assert data["visceral_fat"] == 13

    def test_parse_null_values(self, tmp_path):
        """Rows with null composition still import weight."""
        csv_content = """time,weight,height,bmi,fatRate,bodyWaterRate,boneMass,metabolism,muscleRate,visceralFat
2025-12-29 05:43:00+0000,78.3,175.0,25.5,null,null,null,null,null,null"""
        csv_file = tmp_path / "body.csv"
        csv_file.write_text(csv_content)
        
        result = parse_scale_csv(str(csv_file))
        data = result["2025-12-29"]
        assert data["weight_kg"] == 78.3
        assert "body_fat_pct" not in data

    def test_overwrite_logic(self, tmp_path):
        """Row with composition should overwrite row without, regardless of order."""
        # 1. Null first, then data
        csv_content = """time,weight,fatRate
2025-12-29 05:42:00+0000,78.0,null
2025-12-29 05:43:00+0000,78.3,25.6"""
        csv_file = tmp_path / "body.csv"
        csv_file.write_text(csv_content)
        
        result = parse_scale_csv(str(csv_file))
        assert result["2025-12-29"]["weight_kg"] == 78.3
        assert result["2025-12-29"]["body_fat_pct"] == 25.6
