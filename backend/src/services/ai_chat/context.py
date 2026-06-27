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
    try:
        progress = build_progress_snapshot(plan, database) if plan else None
        plan_snapshot = build_plan_prompt_snapshot(plan, discovery, progress)
        plan_summary = format_plan_snapshot(plan_snapshot)
        plan_status = getattr(plan_snapshot, "status", "NO_PLAN")
        plan_discovery = getattr(plan_snapshot, "discovery", None)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to load plan context for %s: %s", user_email, exc)
        plan_summary = ""
        plan_status = "NO_PLAN"
        plan_discovery = None

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
    }
