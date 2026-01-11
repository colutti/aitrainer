import pytest
from datetime import date
from pydantic import ValidationError
from src.api.models.weight_log import WeightLog

class TestWeightLogModel:
    def test_minimal_valid(self):
        """Backwards compatibility: only required fields."""
        log = WeightLog(user_email="test@test.com", date=date.today(), weight_kg=75.0)
        assert log.body_fat_pct is None
        assert log.source is None

    def test_full_composition(self):
        """All body composition fields populated."""
        log = WeightLog(
            user_email="test@test.com",
            date=date.today(),
            weight_kg=76.8,
            body_fat_pct=24.2,
            muscle_mass_pct=55.2,
            bone_mass_kg=2.96,
            body_water_pct=52.0,
            visceral_fat=13.0, # Now float
            bmr=1492,
            bmi=25.0,
            source="scale_import"
        )
        assert log.body_fat_pct == 24.2
        assert log.bmr == 1492

    def test_validation_body_fat_range(self):
        """Body fat must be 0-100."""
        with pytest.raises(ValidationError):
            WeightLog(user_email="x", date=date.today(), weight_kg=75, body_fat_pct=150)

    def test_validation_visceral_fat_range(self):
        """Visceral fat must be 0-50."""
        with pytest.raises(ValidationError):
            WeightLog(user_email="x", date=date.today(), weight_kg=75, visceral_fat=60)
