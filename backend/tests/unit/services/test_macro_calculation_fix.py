"""
Test-Driven Development: Macro calculation should validate that total calories = target
This is the FAILING test that will drive the implementation.
"""

import pytest
from src.services.adaptive_tdee import AdaptiveTDEEService
from unittest.mock import MagicMock


@pytest.fixture
def service():
    db = MagicMock()
    return AdaptiveTDEEService(db)


class TestMacroCalculationValidation:
    """
    These tests define the CORRECT behavior:
    - Macros must sum to daily_target (within small rounding)
    - Protein should scale intelligently with goal type
    - No macro should be completely eliminated
    """

    def test_macro_sum_equals_target_extreme_weight_low_calories(self, service):
        """
        CRITICAL: Extreme case that currently FAILS
        150kg person, 1200 kcal target
        Expected: Macros should sum to ~1200 kcal, not 1500 kcal
        """
        macros = service._calculate_macro_targets(daily_target=1200, weight_kg=150)

        total_kcal = (macros["protein"] * 4 +
                      macros["carbs"] * 4 +
                      macros["fat"] * 9)

        # Allow ±5% for rounding (50-60 kcal variance)
        assert 1140 <= total_kcal <= 1260, (
            f"Macros sum to {total_kcal}kcal, not ~1200kcal. "
            f"P:{macros['protein']}g F:{macros['fat']}g C:{macros['carbs']}g"
        )

    def test_macro_sum_equals_target_high_weight_low_calories(self, service):
        """
        200kg person, 1500 kcal target
        Expected: Macros should sum to ~1500 kcal, not 1978 kcal
        """
        macros = service._calculate_macro_targets(daily_target=1500, weight_kg=200)

        total_kcal = (macros["protein"] * 4 +
                      macros["carbs"] * 4 +
                      macros["fat"] * 9)

        assert 1425 <= total_kcal <= 1575, (
            f"Macros sum to {total_kcal}kcal, not ~1500kcal"
        )

    def test_macro_sum_equals_target_normal_case(self, service):
        """
        80kg person, 2500 kcal target (normal case)
        Expected: Macros should sum to ~2500 kcal
        """
        macros = service._calculate_macro_targets(daily_target=2500, weight_kg=80)

        total_kcal = (macros["protein"] * 4 +
                      macros["carbs"] * 4 +
                      macros["fat"] * 9)

        assert 2375 <= total_kcal <= 2625, (
            f"Macros sum to {total_kcal}kcal, not ~2500kcal"
        )

    def test_no_macros_are_zero_unless_necessary(self, service):
        """
        Even in extreme cases, each macro should have at least some grams
        (unless they absolutely can't fit)
        """
        # Extreme: high weight, very low calories
        macros = service._calculate_macro_targets(daily_target=1000, weight_kg=120)

        # All should have values (carbs might be minimal but not 0)
        assert macros["protein"] > 0
        assert macros["fat"] > 0
        # Carbs can be 0 if truly constrained, but let's check the logic

    def test_protein_respects_calorie_limit(self, service):
        """
        Protein should never consume more than 60% of daily target
        (leaving room for fats and carbs)
        """
        test_cases = [
            (100, 1200),
            (150, 1200),
            (200, 1500),
        ]

        for weight_kg, daily_target in test_cases:
            macros = service._calculate_macro_targets(daily_target, weight_kg)
            protein_kcal = macros["protein"] * 4

            protein_pct = (protein_kcal / daily_target) * 100 if daily_target > 0 else 0

            assert protein_pct <= 60, (
                f"Protein {protein_pct:.1f}% of daily target - too high! "
                f"Weight:{weight_kg}kg Target:{daily_target}kcal"
            )

    def test_macros_with_wide_calorie_range(self, service):
        """
        Test macro calculation across the full range of typical daily targets
        """
        weight = 85  # Fixed weight for consistency
        targets = [1200, 1500, 1800, 2000, 2500, 3000]

        for target in targets:
            macros = service._calculate_macro_targets(target, weight)
            total = macros["protein"] * 4 + macros["carbs"] * 4 + macros["fat"] * 9

            # Should be within 5% of target for all cases
            diff_pct = abs(total - target) / target * 100
            assert diff_pct <= 5, (
                f"Target {target}kcal: Macros sum to {total}kcal "
                f"(off by {diff_pct:.1f}%). P:{macros['protein']}g "
                f"C:{macros['carbs']}g F:{macros['fat']}g"
            )
