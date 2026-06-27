"""Context loading for one chat turn."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.core.config import settings
from src.core.logs import logger
from src.repositories.event_repository import EventRepository
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.services.plan_service import (
    build_plan_prompt_snapshot,
    build_progress_snapshot,
    format_plan_snapshot,
)


def _safe_number(value) -> int | float | None:
    """Return a JSON-friendly numeric value when one is available."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _get_attr_or_key(source, name: str, default=None):
    """Read from a Pydantic model, object, or dict without caring about shape."""
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def _macro_target(nutrition_stats, key: str) -> int | float | None:
    targets = _get_attr_or_key(nutrition_stats, "macro_targets", None) or {}
    if not isinstance(targets, dict):
        return None
    candidates = (key, f"{key}_g", key.replace("_g", ""))
    for candidate in candidates:
        value = targets.get(candidate)
        if (number := _safe_number(value)) is not None:
            return number
    return None


def _suggest_decision(progress, nutrition_stats, metabolism_data: dict) -> str:
    decision = "maintain"
    if progress is None:
        decision = "collect_data"
    elif getattr(progress, "conflicts", None):
        decision = "formal_plan_review"
    else:
        training_status = getattr(progress.training_adherence, "status", "insufficient_data")
        nutrition_status = getattr(progress.nutrition_adherence, "status", "insufficient_data")
        body_status = getattr(progress, "body_trend_status", "insufficient_data")
        progression_status = getattr(progress, "progression_status", "insufficient_data")
        logged_days = int(_get_attr_or_key(nutrition_stats, "total_logs", 0) or 0)
        tdee = _safe_number((metabolism_data or {}).get("tdee"))

        if "insufficient_data" in {training_status, nutrition_status} or logged_days == 0:
            decision = "collect_data"
        elif training_status == "off_track" or nutrition_status == "off_track":
            decision = "coach_adherence"
        elif (
            progression_status in {"stalled", "regressing"}
            and body_status != "insufficient_data"
        ):
            decision = "small_adjustment"
        elif tdee is None and body_status == "insufficient_data":
            decision = "collect_data"
    return decision


def _build_coaching_snapshot(
    *,
    progress,
    nutrition_stats,
    weight_logs: list,
    metabolism_data: dict,
    progress_failed: bool,
) -> dict:
    """Build a compact, signal-oriented context block for coach decisions."""
    gaps = []
    if progress is None:
        gaps.append("plan_progress" if progress_failed else "training")
        if progress_failed:
            gaps.extend(["training", "nutrition", "body"])
    else:
        if progress.training_adherence.status == "insufficient_data":
            gaps.append("training")
        if progress.nutrition_adherence.status == "insufficient_data":
            gaps.append("nutrition")
        if progress.body_trend_status == "insufficient_data":
            gaps.append("body")
    if not metabolism_data:
        gaps.append("metabolism")

    logged_days = int(_get_attr_or_key(nutrition_stats, "total_logs", 0) or 0)
    avg_calories = _safe_number(_get_attr_or_key(nutrition_stats, "avg_daily_calories", None))
    avg_protein = _safe_number(_get_attr_or_key(nutrition_stats, "avg_protein", None))
    calorie_target = _safe_number(_get_attr_or_key(nutrition_stats, "daily_target", None))
    protein_target = _macro_target(nutrition_stats, "protein")
    tdee = _safe_number((metabolism_data or {}).get("tdee"))
    tdee_confidence = (metabolism_data or {}).get("confidence")

    confidence = "high"
    if len(set(gaps)) >= 3:
        confidence = "low"
    elif gaps:
        confidence = "medium"

    conflicts = []
    if progress is not None:
        conflicts = [
            getattr(conflict, "message", str(conflict))
            for conflict in getattr(progress, "conflicts", [])
        ]

    return {
        "data_quality": {
            "confidence": confidence,
            "gaps": sorted(set(gaps)),
        },
        "adherence": {
            "training": {
                "status": (
                    getattr(progress.training_adherence, "status", "insufficient_data")
                    if progress is not None
                    else "insufficient_data"
                ),
                "details": (
                    getattr(progress.training_adherence, "details", "Sem dados suficientes.")
                    if progress is not None
                    else "Sem dados suficientes."
                ),
            },
            "nutrition": {
                "status": (
                    getattr(progress.nutrition_adherence, "status", "insufficient_data")
                    if progress is not None
                    else "insufficient_data"
                ),
                "logged_days": logged_days,
                "avg_calories": avg_calories,
                "calorie_target": calorie_target,
                "avg_protein": avg_protein,
                "protein_target": protein_target,
            },
        },
        "progression": {
            "status": (
                getattr(progress, "progression_status", "insufficient_data")
                if progress is not None
                else "insufficient_data"
            ),
            "evidence": (
                list(getattr(progress, "evidence_summary", []))[:3]
                if progress is not None
                else []
            ),
        },
        "recovery_risk": {
            "conflicts": conflicts[:3],
            "recommended_review": bool(
                getattr(progress, "recommended_review", False)
                if progress is not None
                else False
            ),
        },
        "metabolism_body": {
            "tdee": tdee,
            "tdee_confidence": tdee_confidence,
            "weight_logs": len(weight_logs),
            "body_trend": (
                getattr(progress, "body_trend_status", "insufficient_data")
                if progress is not None
                else "insufficient_data"
            ),
        },
        "decision": {
            "suggested_action": _suggest_decision(progress, nutrition_stats, metabolism_data),
        },
    }


def build_runtime_context(
    # pylint: disable=too-many-locals
    *,
    database,
    user_email: str,
    profile,
    trainer_profile,
    is_telegram: bool = False,
) -> dict:
    """Build the structured runtime context passed to the agent."""
    timezone_name = getattr(profile, "timezone", None) or "Europe/Madrid"
    try:
        now = datetime.now(ZoneInfo(timezone_name))
    except ZoneInfoNotFoundError:
        timezone_name = "UTC"
        now = datetime.now(timezone.utc)

    try:
        metabolism_data = AdaptiveTDEEService(database).calculate_tdee(user_email)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load metabolism context for %s: %s", user_email, exc)
        metabolism_data = {}

    plan = database.get_plan(user_email) if hasattr(database, "get_plan") else None
    discovery = (
        database.get_plan_discovery(user_email)
        if hasattr(database, "get_plan_discovery")
        else None
    )
    progress = None
    progress_failed = False
    try:
        progress = build_progress_snapshot(plan, database) if plan else None
        plan_snapshot = build_plan_prompt_snapshot(plan, discovery, progress)
        plan_summary = format_plan_snapshot(plan_snapshot)
        plan_status = getattr(plan_snapshot, "status", "NO_PLAN")
        plan_discovery = getattr(plan_snapshot, "discovery", None)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load plan context for %s: %s", user_email, exc)
        progress_failed = True
        plan_summary = ""
        plan_status = "NO_PLAN"
        plan_discovery = None

    try:
        nutrition_stats = database.get_nutrition_stats(user_email)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load nutrition context for %s: %s", user_email, exc)
        nutrition_stats = {}

    try:
        weight_logs = database.get_weight_logs(user_email, limit=30)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load body context for %s: %s", user_email, exc)
        weight_logs = []

    coaching_snapshot = _build_coaching_snapshot(
        progress=progress,
        nutrition_stats=nutrition_stats,
        weight_logs=weight_logs,
        metabolism_data=metabolism_data or {},
        progress_failed=progress_failed,
    )

    try:
        agenda = EventRepository(database.database).get_active_events(user_email)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load agenda context for %s: %s", user_email, exc)
        agenda = []

    return {
        "contract_version": settings.PROMPT_CONTEXT_CONTRACT_VERSION,
        "session": {
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "day_of_week": now.strftime("%A"),
            "user_timezone": timezone_name,
            "channel": "telegram" if is_telegram else "app",
        },
        "trainer": {
            "name": getattr(trainer_profile, "trainer_type", "atlas"),
            "trainer_type": getattr(trainer_profile, "trainer_type", "atlas"),
            "preferred_language": getattr(trainer_profile, "preferred_language", None)
            or "pt-BR",
            "profile": trainer_profile.get_trainer_profile_summary()
            if hasattr(trainer_profile, "get_trainer_profile_summary")
            else str(trainer_profile),
        },
        "user": {
            "email": user_email,
            "name": getattr(profile, "display_name", None) or "Aluno",
            "profile": profile.get_profile_summary()
            if hasattr(profile, "get_profile_summary")
            else str(profile),
        },
        "agenda": {
            "events": [
                event.model_dump() if hasattr(event, "model_dump") else str(event)
                for event in agenda
            ],
        },
        "metabolism": metabolism_data or {},
        "plan": {
            "summary": plan_summary,
            "status": plan_status,
            "has_active_plan": plan_status == "ACTIVE_PLAN",
            "discovery": plan_discovery,
        },
        "prompt_context_v2": {
            "coaching_snapshot": coaching_snapshot,
        },
    }
