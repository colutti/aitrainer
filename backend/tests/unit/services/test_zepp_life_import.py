from datetime import date
from src.services.zepp_life_import_service import (
    parse_zepp_life_csv,
    import_zepp_life_data,
)
from src.api.models.weight_log import WeightLog
from unittest.mock import MagicMock

# Sample CSV content
SAMPLE_CSV = """time,weight,fatRate,muscleRate,boneMass,bodyWaterRate,visceralFat,metabolism,bmi
2025-01-01 08:00:00+0000,80.5,20.0,55.0,3.0,60.0,10,1800,25.0
2025-01-02 08:00:00+0000,80.0,19.8,55.2,3.0,60.2,9,1790,24.8
"""

SAMPLE_CSV_WITH_NULLS = """time,weight,fatRate,muscleRate,boneMass,bodyWaterRate,visceralFat,metabolism,bmi
2025-01-03 08:00:00+0000,79.5,null,null,null,null,null,null,24.5
"""


def test_parse_zepp_life_csv_valid():
    """Test parsing a valid CSV."""
    data = parse_zepp_life_csv(SAMPLE_CSV)
    assert len(data) == 2

    day1 = data["2025-01-01"]
    assert day1["weight_kg"] == 80.5
    assert day1["body_fat_pct"] == 20.0
    assert day1["visceral_fat"] == 10

    day2 = data["2025-01-02"]
    assert day2["weight_kg"] == 80.0


def test_parse_zepp_life_csv_with_nulls():
    """Test parsing CSV with null values."""
    data = parse_zepp_life_csv(SAMPLE_CSV_WITH_NULLS)
    assert len(data) == 1
    day3 = data["2025-01-03"]
    assert day3["weight_kg"] == 79.5
    assert "body_fat_pct" not in day3


def test_parse_zepp_life_csv_duplicate_logic():
    """
    Test logic for duplicates on same day.
    Row 1: Full data
    Row 2: Weight only (later time)
    Should keep Row 1 because it has composition data, even if Row 2 is later (if the logic dictates so,
    but the service implementation says: 'If current row has missing composition data (nulls), but existing data HAS composition, keep existing composition.')
    """
    # Note: dict order preservation depends on python version but here we rely on the logic inside the loop
    csv_content = """time,weight,fatRate
2025-01-01 08:00:00,80.0,20.0
2025-01-01 10:00:00,81.0,null
"""
    data = parse_zepp_life_csv(csv_content)
    assert len(data) == 1
    day1 = data["2025-01-01"]

    # Should contain the first one because the second one lacks fatRate
    assert day1["weight_kg"] == 80.0
    assert day1["body_fat_pct"] == 20.0


def test_import_zepp_life_data():
    """Test the full import service function."""
    mock_db = MagicMock()
    # Setup mock to return (doc_id, is_new)
    mock_db.save_weight_log.side_effect = [("id1", True), ("id2", False)]

    result = import_zepp_life_data("test@example.com", SAMPLE_CSV, mock_db)

    assert result.created == 1
    assert result.updated == 1
    assert result.errors == 0
    assert result.total_days == 2

    # Verify DB calls
    assert mock_db.save_weight_log.call_count == 2

    # Check first call args
    call_args = mock_db.save_weight_log.call_args_list[0]
    log = call_args[0][0]
    assert isinstance(log, WeightLog)
    assert log.user_email == "test@example.com"
    assert log.date == date(2025, 1, 1)
    assert log.weight_kg == 80.5
    assert log.source == "zepp_life_import"
