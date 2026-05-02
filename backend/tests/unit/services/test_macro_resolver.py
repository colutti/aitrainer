"""Tests for macro target resolution (plan-first, TDEE fallback)."""

from src.services.macro_resolver import resolve_macro_targets


def test_returns_plan_macros_when_plan_has_all_macros():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": 180,
        "carbs_g": 200,
        "fat_g": 70,
    }
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["protein"] == 180
    assert result["carbs"] == 200
    assert result["fat"] == 70
    assert result["source"] == "plan"


def test_returns_fallback_macros_when_no_plan():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    result = resolve_macro_targets(tdee_macros=tdee_macros, plan_daily_targets=None)
    assert result["protein"] == 128
    assert result["carbs"] == 202
    assert result["fat"] == 54
    assert result["source"] == "fallback"


def test_returns_fallback_when_plan_has_no_macro_targets():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {"calories": 2200}
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128


def test_returns_fallback_when_plan_missing_carbs():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": 180,
        "fat_g": 70,
    }
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128


def test_returns_fallback_when_plan_missing_fat():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": 180,
        "carbs_g": 200,
    }
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128


def test_returns_fallback_when_plan_has_zero_macros():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": 0,
        "carbs_g": 0,
        "fat_g": 0,
    }
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128


def test_returns_plan_macros_with_none_tdee():
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": 180,
        "carbs_g": 200,
        "fat_g": 70,
    }
    result = resolve_macro_targets(tdee_macros=None, plan_daily_targets=plan_daily_targets)
    assert result["protein"] == 180
    assert result["carbs"] == 200
    assert result["fat"] == 70
    assert result["source"] == "plan"


def test_returns_none_when_both_null():
    result = resolve_macro_targets(tdee_macros=None, plan_daily_targets=None)
    assert result["source"] == "none"
    assert result["protein"] is None
    assert result["carbs"] is None
    assert result["fat"] is None


def test_returns_none_when_empty_tdee_and_no_plan():
    result = resolve_macro_targets(tdee_macros={}, plan_daily_targets=None)
    assert result["source"] == "none"
    assert result["protein"] is None


def test_returns_fallback_for_partial_tdee():
    result = resolve_macro_targets(
        tdee_macros={"protein": 128}, plan_daily_targets=None
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128
    assert result["carbs"] == 0
    assert result["fat"] == 0


def test_handles_plan_with_none_values():
    tdee_macros = {"protein": 128, "carbs": 202, "fat": 54}
    plan_daily_targets = {
        "calories": 2200,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None,
    }
    result = resolve_macro_targets(
        tdee_macros=tdee_macros, plan_daily_targets=plan_daily_targets
    )
    assert result["source"] == "fallback"
    assert result["protein"] == 128
