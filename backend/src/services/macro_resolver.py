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
