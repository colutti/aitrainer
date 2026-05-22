"""Resolve daily macro targets from plan or TDEE algorithm.

If the active plan has complete macro targets (protein_g, carbs_g, fat_g all > 0),
those take precedence. Otherwise fall back to TDEE algorithm macros.

Note: Existing plans created before this change may have carbs_g and fat_g as null.
The resolver handles this by falling back to TDEE macros for incomplete plan targets.
"""

from __future__ import annotations

from typing import Any


def resolve_macro_targets(
    tdee_macros: dict[str, int] | None,
    plan_daily_targets: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return the effective macro targets and their source.

    Priority: plan macros (if all three macros are present and > 0) > TDEE fallback.

    Returns dict with keys: protein, carbs, fat, source ("plan" | "fallback" | "none").
    """
    plan_has_all_macros = (
        plan_daily_targets is not None
        and isinstance(plan_daily_targets.get("protein_g"), (int, float))
        and plan_daily_targets["protein_g"] > 0
        and isinstance(plan_daily_targets.get("carbs_g"), (int, float))
        and plan_daily_targets["carbs_g"] > 0
        and isinstance(plan_daily_targets.get("fat_g"), (int, float))
        and plan_daily_targets["fat_g"] > 0
    )

    if plan_has_all_macros:
        return {
            "protein": int(plan_daily_targets["protein_g"]),
            "carbs": int(plan_daily_targets["carbs_g"]),
            "fat": int(plan_daily_targets["fat_g"]),
            "source": "plan",
        }

    if tdee_macros:
        return {
            "protein": tdee_macros.get("protein", 0),
            "carbs": tdee_macros.get("carbs", 0),
            "fat": tdee_macros.get("fat", 0),
            "source": "fallback",
        }

    return {
        "protein": None,
        "carbs": None,
        "fat": None,
        "source": "none",
    }


def get_plan_daily_targets(plan) -> dict[str, Any] | None:
    """Extract daily targets from a plan-like object when available."""
    if not plan:
        return None

    nutrition_block = getattr(plan, "nutrition", None)
    if nutrition_block is None:
        nutrition_block = getattr(plan, "nutrition_strategy", None)
    if nutrition_block is None:
        return None

    daily_targets = getattr(nutrition_block, "daily_targets", None)
    if not daily_targets:
        return None
    dumped = daily_targets.model_dump(exclude_none=True)
    if "calories_kcal" in dumped and "calories" not in dumped:
        dumped["calories"] = dumped["calories_kcal"]
    return dumped


def resolve_macro_targets_for_plan(
    tdee_macros: dict[str, int] | None,
    plan,
) -> tuple[dict[str, int], str]:
    """Resolve macro targets and normalize the response shape for callers."""
    resolved = resolve_macro_targets(
        tdee_macros=tdee_macros,
        plan_daily_targets=get_plan_daily_targets(plan),
    )
    macro_dict = {
        "protein": resolved["protein"] or 0,
        "carbs": resolved["carbs"] or 0,
        "fat": resolved["fat"] or 0,
    }
    return macro_dict, resolved.get("source", "fallback")
