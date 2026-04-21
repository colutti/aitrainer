"""Builders for enriched coaching context attached to plan prompt snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import re
from typing import Any

from src.api.models.plan import (
    ActivePlan,
    PlanSnapshotAdherence7D,
    PlanSnapshotExerciseContext,
    PlanSnapshotWeightTrend,
)


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
        except ValueError:
            return None
    return None


def _to_date(value: Any) -> date | None:
    as_dt = _as_datetime(value)
    if as_dt is not None:
        return as_dt.date()
    return value if isinstance(value, date) else None


def _normalize_exercise_name(name: str) -> str:
    collapsed = re.sub(r"\s+", " ", name.strip().lower())
    return collapsed


def _extract_today_exercises(plan: ActivePlan) -> list[dict[str, Any]]:
    training = plan.execution.today_training
    if not isinstance(training, dict):
        return []

    session = training.get("session")
    if isinstance(session, dict) and isinstance(session.get("exercises"), list):
        return [
            item
            for item in session["exercises"]
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ]
    direct = training.get("exercises")
    if isinstance(direct, list):
        return [
            item
            for item in direct
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ]
    return []


def _extract_max_positive_weight(exercise: dict[str, Any]) -> float | None:
    weights = exercise.get("weights_per_set")
    if not isinstance(weights, list):
        return None
    valid = [
        float(item)
        for item in weights
        if isinstance(item, (int, float)) and item > 0
    ]
    if not valid:
        return None
    return max(valid)


def _build_exercise_context(
    today_exercises: list[dict[str, Any]],
    workout_logs: list[Any],
    now: datetime,
) -> list[PlanSnapshotExerciseContext]:
    # pylint: disable=too-many-locals
    earliest = now - timedelta(days=90)
    normalized_logs: list[dict[str, Any]] = []
    for log in workout_logs:
        if not isinstance(log, dict):
            continue
        log_date = _as_datetime(log.get("date"))
        if log_date is None or log_date < earliest:
            continue
        normalized_logs.append(
            {"date": log_date, "exercises": log.get("exercises", [])}
        )

    normalized_logs.sort(key=lambda item: item["date"], reverse=True)

    result: list[PlanSnapshotExerciseContext] = []
    for exercise in today_exercises:
        name = str(exercise.get("name"))
        normalized_name = _normalize_exercise_name(name)
        last_load_kg: float | None = None
        last_performed_at: str | None = None

        for workout in normalized_logs:
            matches: list[float] = []
            raw_exercises = workout.get("exercises", [])
            if not isinstance(raw_exercises, list):
                continue
            for logged_exercise in raw_exercises:
                if not isinstance(logged_exercise, dict):
                    continue
                logged_name = logged_exercise.get("name")
                if not isinstance(logged_name, str):
                    continue
                if _normalize_exercise_name(logged_name) != normalized_name:
                    continue
                maybe_weight = _extract_max_positive_weight(logged_exercise)
                if maybe_weight is not None:
                    matches.append(maybe_weight)
            if matches:
                last_load_kg = max(matches)
                last_performed_at = workout["date"].date().isoformat()
                break

        result.append(
            PlanSnapshotExerciseContext(
                exercise_name=name,
                prescribed_sets=(
                    str(exercise.get("sets")) if exercise.get("sets") is not None else None
                ),
                prescribed_reps=(
                    str(exercise.get("reps")) if exercise.get("reps") is not None else None
                ),
                load_guidance=(
                    str(exercise.get("load_guidance"))
                    if exercise.get("load_guidance") is not None
                    else None
                ),
                last_load_kg=last_load_kg,
                last_performed_at=last_performed_at,
            )
        )
    return result


def _get_window(now: datetime) -> tuple[date, date]:
    window_end = now.date()
    window_start = window_end - timedelta(days=6)
    return window_start, window_end


def _calculate_nutrition_adherence(
    nutrition_logs: list[Any], window_start: date, window_end: date
) -> int:
    del window_end  # kept for signature parity/readability
    days_logged: set[date] = set()
    for log in nutrition_logs:
        if isinstance(log, dict):
            log_date = _to_date(log.get("date"))
        else:
            log_date = _to_date(getattr(log, "date", None))
        if log_date is None:
            continue
        if log_date < window_start:
            continue
        days_logged.add(log_date)
    return round((len(days_logged) / 7) * 100)


def _has_training_planned(day_payload: Any) -> bool:
    if not isinstance(day_payload, dict):
        return False
    if day_payload.get("status") == "rest":
        return False
    training = day_payload.get("training")
    if isinstance(training, str):
        return bool(training.strip())
    if isinstance(training, dict):
        if isinstance(training.get("title"), str) and training.get("title").strip():
            return True
        session = training.get("session")
        if isinstance(session, dict) and isinstance(session.get("exercises"), list):
            return len(session["exercises"]) > 0
    return False


def _calculate_training_adherence(
    upcoming_days: list[Any], workout_logs: list[Any], window_start: date, window_end: date
) -> int | None:
    planned_days: set[date] = set()
    for item in upcoming_days:
        if not isinstance(item, dict):
            continue
        date_value = _to_date(item.get("date"))
        if date_value is None:
            continue
        if date_value < window_start or date_value > window_end:
            continue
        if _has_training_planned(item):
            planned_days.add(date_value)
    if not planned_days:
        return None

    executed_days: set[date] = set()
    for log in workout_logs:
        if isinstance(log, dict):
            workout_date = _to_date(log.get("date"))
        else:
            workout_date = _to_date(getattr(log, "date", None))
        if workout_date is None:
            continue
        if workout_date in planned_days:
            executed_days.add(workout_date)

    return round((len(executed_days) / len(planned_days)) * 100)


def _extract_weight_trend(metabolism_data: dict[str, Any]) -> PlanSnapshotWeightTrend | None:
    if "weight_change_per_week" not in metabolism_data:
        return None
    value = metabolism_data.get("weight_change_per_week")
    if not isinstance(value, (int, float)):
        return None
    return PlanSnapshotWeightTrend(
        value_kg_per_week=float(value),
        source="adaptive_tdee",
    )


@dataclass
class PlanSnapshotContext:
    """Structured context merged into PlanSnapshot before prompt formatting."""

    today_training_context: list[PlanSnapshotExerciseContext]
    adherence_7d: PlanSnapshotAdherence7D | None
    weight_trend_weekly: PlanSnapshotWeightTrend | None


def build_plan_snapshot_context(
    *,
    database,
    user_email: str,
    plan: ActivePlan,
    metabolism_data: dict[str, Any],
    now: datetime | None = None,
) -> PlanSnapshotContext:
    """Builds additional coaching context consumed by plan prompt snapshot."""
    current = now or datetime.now()
    window_start, window_end = _get_window(current)

    workout_logs_raw = database.get_workout_logs(user_email, limit=50)
    workout_logs: list[Any]
    if isinstance(workout_logs_raw, list):
        workout_logs = [
            log.model_dump() if hasattr(log, "model_dump") else log
            for log in workout_logs_raw
        ]
    else:
        workout_logs = []

    nutrition_logs_raw = database.get_nutrition_logs_by_date_range(
        user_email,
        datetime.combine(window_start, datetime.min.time()),
        datetime.combine(window_end, datetime.max.time()),
    )
    nutrition_logs = (
        [
            log.model_dump() if hasattr(log, "model_dump") else log
            for log in nutrition_logs_raw
        ]
        if isinstance(nutrition_logs_raw, list)
        else []
    )

    today_exercises = _extract_today_exercises(plan)
    training_context = _build_exercise_context(today_exercises, workout_logs, current)

    adherence = PlanSnapshotAdherence7D(
        training_percent=_calculate_training_adherence(
            plan.execution.upcoming_days,
            workout_logs,
            window_start,
            window_end,
        ),
        nutrition_percent=_calculate_nutrition_adherence(
            nutrition_logs,
            window_start,
            window_end,
        ),
        window_start=window_start.isoformat(),
        window_end=window_end.isoformat(),
    )

    return PlanSnapshotContext(
        today_training_context=training_context,
        adherence_7d=adherence,
        weight_trend_weekly=_extract_weight_trend(metabolism_data),
    )
