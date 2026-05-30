#!/usr/bin/env python3
"""Migrate legacy plan documents to plan_v2."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pydantic import ValidationError

# Allow execution from backend/ like other project scripts.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.api.models.plan import (
    ConflictRule,
    IntensityPrescription,
    PlanAlignment,
    PlanGoal,
    PlanNutrition,
    PlanReview,
    PlanTimeline,
    PlanTracking,
    PlanUserContext,
    PrimaryGoal,
    ProgressMarker,
    ProgressionRule,
    RepRange,
    SuccessMetric,
    TrainingExercise,
    TrainingRoutine,
    UserPlan,
    WeeklyScheduleItem,
)
from src.core.config import settings


CANONICAL_WEEKDAYS = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)

WEEKDAY_ALIASES = {
    "monday": "monday",
    "mon": "monday",
    "segunda": "monday",
    "segunda-feira": "monday",
    "tuesday": "tuesday",
    "tue": "tuesday",
    "terca": "tuesday",
    "terça": "tuesday",
    "terca-feira": "tuesday",
    "terça-feira": "tuesday",
    "wednesday": "wednesday",
    "wed": "wednesday",
    "quarta": "wednesday",
    "quarta-feira": "wednesday",
    "thursday": "thursday",
    "thu": "thursday",
    "quinta": "thursday",
    "quinta-feira": "thursday",
    "friday": "friday",
    "fri": "friday",
    "sexta": "friday",
    "sexta-feira": "friday",
    "saturday": "saturday",
    "sat": "saturday",
    "sabado": "saturday",
    "sábado": "saturday",
    "sunday": "sunday",
    "sun": "sunday",
    "domingo": "sunday",
}

CADENCE_DAYS = {
    "semanal": 7,
    "weekly": 7,
    "quinzenal": 15,
    "biweekly": 15,
    "mensal": 30,
    "monthly": 30,
}

GOAL_MAP: dict[str, PrimaryGoal] = {
    "lose_fat": "fat_loss",
    "fat_loss": "fat_loss",
    "build_muscle": "muscle_gain",
    "muscle_gain": "muscle_gain",
    "recomposition": "recomposition",
    "performance": "performance",
    "health": "health",
}


@dataclass
class MigrationResult:
    user_email: str
    schema_before: str
    status: str
    warnings: list[str]
    errors: list[str]


def _to_date(value: Any, field_name: str, warnings: list[str]) -> date:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        raw = value.strip()
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                return date.fromisoformat(raw)
            except ValueError as exc:
                raise ValueError(f"invalid {field_name}: {value}") from exc
    warnings.append(f"{field_name} missing; defaulting to today")
    return date.today()


def _normalize_weekday(value: Any, warnings: list[str]) -> str:
    if not isinstance(value, str):
        warnings.append("non-string weekday found; defaulting to monday")
        return "monday"
    normalized = value.strip().lower()
    normalized = normalized.replace("ç", "c")
    normalized = normalized.replace("á", "a").replace("à", "a").replace("â", "a").replace("ã", "a")
    normalized = normalized.replace("é", "e").replace("ê", "e")
    normalized = normalized.replace("í", "i")
    normalized = normalized.replace("ó", "o").replace("ô", "o").replace("õ", "o")
    normalized = normalized.replace("ú", "u")
    return WEEKDAY_ALIASES.get(normalized, normalized if normalized in CANONICAL_WEEKDAYS else "monday")


def _parse_rep_range(raw: Any) -> RepRange:
    if isinstance(raw, int):
        return RepRange(min_reps=raw, max_reps=raw)
    if isinstance(raw, float):
        parsed = int(raw)
        return RepRange(min_reps=parsed, max_reps=parsed)
    if isinstance(raw, list):
        nums = [int(x) for x in raw if isinstance(x, (int, float, str)) and str(x).strip().isdigit()]
        if not nums:
            raise ValueError(f"cannot parse reps from list: {raw}")
        return RepRange(min_reps=min(nums), max_reps=max(nums))
    if isinstance(raw, str):
        text = raw.strip()
        if text.isdigit():
            val = int(text)
            return RepRange(min_reps=val, max_reps=val)
        nums = [int(n) for n in re.findall(r"\d+", text)]
        if not nums:
            raise ValueError(f"cannot parse reps from string: {raw}")
        if len(nums) == 1:
            return RepRange(min_reps=nums[0], max_reps=nums[0])
        return RepRange(min_reps=min(nums), max_reps=max(nums))
    raise ValueError(f"unsupported reps value: {raw}")


def _energy_strategy(primary_goal: PrimaryGoal) -> str:
    if primary_goal == "muscle_gain":
        return "surplus"
    if primary_goal == "fat_loss":
        return "deficit"
    if primary_goal == "recomposition":
        return "recomposition"
    return "maintenance"


def _derive_goal(legacy_goal: dict[str, Any], warnings: list[str]) -> tuple[PlanGoal, PrimaryGoal]:
    primary_raw = str(legacy_goal.get("primary", "")).strip().lower()
    primary_goal = GOAL_MAP.get(primary_raw, "health")
    if primary_goal == "health" and primary_raw and primary_raw not in GOAL_MAP:
        warnings.append(f"unknown legacy goal.primary '{primary_raw}', mapped to health")

    outcome = (legacy_goal.get("objective_summary") or "").strip() or "Plano migrado do schema legado."

    success_metrics: list[SuccessMetric] = []
    for criterion in legacy_goal.get("success_criteria") or []:
        if not isinstance(criterion, str) or not criterion.strip():
            continue
        success_metrics.append(
            SuccessMetric(
                metric_name=criterion.strip(),
                target_value="ver descricao",
                unit="qualitative",
                direction="complete",
            )
        )

    metric_targets = legacy_goal.get("metric_targets") or {}
    weekly_delta = metric_targets.get("weekly_weight_change_kg")
    if isinstance(weekly_delta, (int, float)):
        direction = "increase" if primary_goal == "muscle_gain" else "decrease" if primary_goal == "fat_loss" else "maintain"
        success_metrics.append(
            SuccessMetric(
                metric_name="weekly_weight_change_kg",
                target_value=abs(float(weekly_delta)),
                unit="kg/week",
                direction=direction,
            )
        )

    target_weight = metric_targets.get("target_weight_kg")
    if isinstance(target_weight, (int, float)):
        direction = "increase" if primary_goal == "muscle_gain" else "decrease" if primary_goal == "fat_loss" else "maintain"
        success_metrics.append(
            SuccessMetric(
                metric_name="target_weight",
                target_value=float(target_weight),
                unit="kg",
                direction=direction,
            )
        )

    if not success_metrics:
        success_metrics.append(
            SuccessMetric(
                metric_name="Objetivo principal",
                target_value="concluir",
                unit="qualitative",
                direction="complete",
            )
        )

    return PlanGoal(primary_goal=primary_goal, outcome_summary=outcome, success_metrics=success_metrics), primary_goal


def _build_training(legacy_training: dict[str, Any], warnings: list[str]) -> tuple[dict[str, Any], list[str]]:
    routines_out: list[TrainingRoutine] = []
    routine_ids: set[str] = set()
    for idx, routine in enumerate(legacy_training.get("routines") or []):
        if not isinstance(routine, dict):
            warnings.append(f"routine[{idx}] ignored: not an object")
            continue
        routine_id = str(routine.get("id") or f"routine_{idx+1}").strip()
        routine_id = routine_id or f"routine_{idx+1}"
        if routine_id in routine_ids:
            routine_id = f"{routine_id}_{idx+1}"
        routine_ids.add(routine_id)
        exercises_out: list[TrainingExercise] = []
        for ex_idx, exercise in enumerate(routine.get("exercises") or []):
            if not isinstance(exercise, dict):
                warnings.append(f"routine[{routine_id}].exercise[{ex_idx}] ignored: not an object")
                continue
            name = str(exercise.get("name") or "").strip()
            if not name:
                warnings.append(f"routine[{routine_id}].exercise[{ex_idx}] ignored: empty name")
                continue
            sets = exercise.get("sets")
            if not isinstance(sets, int) or sets <= 0:
                warnings.append(f"routine[{routine_id}].exercise[{name}] invalid sets; defaulting to 3")
                sets = 3
            rep_range = _parse_rep_range(exercise.get("reps"))
            load_guidance = str(exercise.get("load_guidance") or "RPE 7-8")
            exercises_out.append(
                TrainingExercise(
                    name=name,
                    external_exercise_template_id=None,
                    sets=sets,
                    rep_range=rep_range,
                    intensity=IntensityPrescription(prescription_type="guidance", target=load_guidance),
                    rest_seconds=exercise.get("rest_seconds") if isinstance(exercise.get("rest_seconds"), int) else None,
                    progression_rule=ProgressionRule(
                        method="double_progression",
                        increase_when="Complete the top of the rep range with solid form",
                        hold_when="Still building consistency in the prescribed range",
                        deload_when="Form regresses or fatigue accumulates for multiple sessions",
                    ),
                    notes=str(exercise.get("notes")) if exercise.get("notes") is not None else None,
                )
            )
        if not exercises_out:
            raise ValueError(f"routine '{routine_id}' has no valid exercises after migration")
        routines_out.append(
            TrainingRoutine(
                id=routine_id,
                name=str(routine.get("name") or routine_id),
                objective=str(routine.get("objective")) if routine.get("objective") is not None else None,
                exercises=exercises_out,
                external_bindings=[],
            )
        )

    if not routines_out:
        raise ValueError("no routines available after migration")

    schedule_by_day: dict[str, WeeklyScheduleItem] = {}
    actions: list[str] = []
    for item in legacy_training.get("weekly_schedule") or []:
        if not isinstance(item, dict):
            continue
        day = _normalize_weekday(item.get("day"), warnings)
        focus = str(item.get("focus") or "treino").strip() or "treino"
        raw_type = str(item.get("type") or "training").strip().lower()
        routine_id_raw = item.get("routine_id")
        routine_id = str(routine_id_raw).strip() if routine_id_raw is not None else None
        if routine_id and routine_id not in routine_ids:
            warnings.append(f"schedule[{day}] dropped unknown routine_id '{routine_id}'")
            routine_id = None
        entry_type = "off" if (raw_type == "off" or not routine_id) else "training"
        current = WeeklyScheduleItem(day=day, routine_id=routine_id if entry_type == "training" else None, focus=focus, type=entry_type)
        previous = schedule_by_day.get(day)
        if previous is None:
            schedule_by_day[day] = current
            continue
        if previous.type == "off" and current.type == "training":
            schedule_by_day[day] = current
            actions.append(f"day={day} replaced off with training")
        elif previous.type == "training" and current.type == "off":
            actions.append(f"day={day} kept training and dropped off")
        else:
            actions.append(f"day={day} dropped duplicate {current.type}")

    weekly_schedule = [schedule_by_day[d] for d in CANONICAL_WEEKDAYS if d in schedule_by_day]
    if not weekly_schedule:
        raise ValueError("weekly_schedule empty after normalization")
    frequency = sum(1 for entry in weekly_schedule if entry.type == "training")
    if frequency <= 0:
        raise ValueError("no training days after normalization")

    return (
        {
            "split_name": str(legacy_training.get("split_name") or "Plano migrado"),
            "frequency_per_week": frequency,
            "session_duration_min": int(legacy_training.get("session_duration_min") or 60),
            "routines": routines_out,
            "weekly_schedule": weekly_schedule,
        },
        actions,
    )


def _build_review_objects(
    checkpoints: list[dict[str, Any]],
    current_summary: dict[str, Any],
    warnings: list[str],
) -> tuple[list[PlanReview], PlanReview | None]:
    history: list[PlanReview] = []
    for cp in checkpoints:
        if not isinstance(cp, dict):
            continue
        reviewed_at_raw = cp.get("checkpoint_at")
        reviewed_at = datetime.now(timezone.utc)
        if isinstance(reviewed_at_raw, datetime):
            reviewed_at = reviewed_at_raw if reviewed_at_raw.tzinfo else reviewed_at_raw.replace(tzinfo=timezone.utc)
        elif isinstance(reviewed_at_raw, str):
            try:
                parsed = datetime.fromisoformat(reviewed_at_raw.replace("Z", "+00:00"))
                reviewed_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                warnings.append(f"invalid checkpoint_at '{reviewed_at_raw}', using now()")
        next_review_at = None
        next_review_raw = current_summary.get("next_review")
        if next_review_raw is not None:
            try:
                next_review_at = _to_date(next_review_raw, "current_summary.next_review", warnings)
            except ValueError:
                next_review_at = None
        history.append(
            PlanReview(
                reviewed_at=reviewed_at,
                summary=str(cp.get("summary") or "Revisao migrada"),
                decision=str(cp.get("decision") or "keep"),
                changes_made=[],
                next_review_at=next_review_at,
                evidence_summary=[str(e) for e in (cp.get("evidence") or []) if str(e).strip()],
            )
        )
    if history:
        history.sort(key=lambda item: item.reviewed_at)
        return history, history[-1]

    last_review = current_summary.get("last_review")
    if last_review:
        reviewed_at = datetime.now(timezone.utc)
        if isinstance(last_review, str):
            try:
                parsed = datetime.fromisoformat(last_review.replace("Z", "+00:00"))
                reviewed_at = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                warnings.append(f"invalid current_summary.last_review '{last_review}', using now()")
        synthetic = PlanReview(
            reviewed_at=reviewed_at,
            summary="Revisao sintetica criada durante migracao",
            decision="keep",
            changes_made=[],
            next_review_at=_to_date(current_summary.get("next_review"), "current_summary.next_review", warnings)
            if current_summary.get("next_review")
            else None,
            evidence_summary=[],
        )
        return [synthetic], synthetic
    return [], None


def migrate_legacy_doc(doc: dict[str, Any]) -> tuple[UserPlan, dict[str, Any]]:
    warnings: list[str] = []
    user_email = str(doc.get("user_email") or "").strip().lower()
    if not user_email:
        raise ValueError("missing user_email")

    legacy_goal = doc.get("goal") or {}
    goal, primary_goal = _derive_goal(legacy_goal, warnings)

    timeline_src = doc.get("timeline") or {}
    current_summary = doc.get("current_summary") or {}
    timeline = PlanTimeline(
        start_date=_to_date(timeline_src.get("start_date"), "timeline.start_date", warnings),
        target_date=_to_date(timeline_src.get("target_date"), "timeline.target_date", warnings),
        review_cadence_days=CADENCE_DAYS.get(str(timeline_src.get("review_cadence") or "").strip().lower(), 14),
        current_phase=str(current_summary.get("active_focus") or "Plano migrado do schema legado"),
    )

    training_payload, schedule_actions = _build_training(doc.get("training_program") or {}, warnings)
    warnings.extend(schedule_actions)
    training_days_available = [entry.day for entry in training_payload["weekly_schedule"] if entry.type == "training"]

    strategy = doc.get("strategy") or {}
    nutrition_strategy = doc.get("nutrition_strategy") or {}
    daily_targets = (nutrition_strategy.get("daily_targets") or {})

    user_context = PlanUserContext(
        training_days_available=training_days_available,
        session_duration_min=training_payload["session_duration_min"],
        constraints=[str(x) for x in (strategy.get("constraints") or []) if str(x).strip()],
        preferences=[str(x) for x in (strategy.get("preferences") or []) if str(x).strip()],
        available_equipment=["unknown"],
        training_level="unknown",
        nutrition_preferences=[str(x) for x in (nutrition_strategy.get("adherence_notes") or []) if str(x).strip()],
    )

    nutrition_text = " ".join(str(x).strip() for x in (nutrition_strategy.get("adherence_notes") or []) if str(x).strip())
    nutrition = PlanNutrition(
        daily_targets={
            "calories_kcal": int(daily_targets.get("calories") or 1800),
            "protein_g": int(daily_targets.get("protein_g") or 120),
            "carbs_g": int(daily_targets.get("carbs_g") or 180),
            "fat_g": int(daily_targets.get("fat_g") or 60),
            "fiber_g": int(daily_targets["fiber_g"]) if isinstance(daily_targets.get("fiber_g"), int) else None,
        },
        strategy=nutrition_text or "Plano nutricional migrado do schema legado.",
        adherence_target_pct=85,
    )

    risks = [str(r).strip() for r in (strategy.get("current_risks") or []) if str(r).strip()]
    conflict_rules = [
        ConflictRule(trigger=risk, action="Revisar o plano e ajustar volume, calorias ou recuperacao.")
        for risk in risks
    ]
    if not conflict_rules:
        conflict_rules = [
            ConflictRule(
                trigger="Dados de progresso ou adesao indicam desalinhamento com o objetivo",
                action="Revisar treino, nutricao e recuperacao antes de manter o plano.",
            )
        ]

    alignment = PlanAlignment(
        training_nutrition_rationale=str(strategy.get("rationale") or "Racional migrado do schema legado."),
        energy_strategy=_energy_strategy(primary_goal),
        recovery_assumptions=risks,
        conflict_rules=conflict_rules,
    )

    tracking = PlanTracking(
        workout_adherence_target_pct=80,
        nutrition_adherence_target_pct=80,
        progress_markers=[
            ProgressMarker(name="Goal Summary", source="manual", target_summary=goal.outcome_summary),
            ProgressMarker(name="Workout Adherence", source="workouts", target_summary="Manter consistencia semanal"),
            ProgressMarker(name="Nutrition Targets", source="nutrition", target_summary="Seguir metas diarias"),
        ],
        review_questions=[
            "Conseguiu seguir os treinos planejados?",
            "Conseguiu seguir as metas nutricionais?",
            "Os dados recentes mostram progresso na direcao do objetivo?",
        ],
    )

    checkpoints = doc.get("checkpoints") or []
    review_history, latest_review = _build_review_objects(checkpoints, current_summary, warnings)

    created_at_raw = doc.get("created_at")
    updated_at_raw = doc.get("updated_at")
    created_at = datetime.now(timezone.utc)
    updated_at = datetime.now(timezone.utc)
    if isinstance(created_at_raw, datetime):
        created_at = created_at_raw if created_at_raw.tzinfo else created_at_raw.replace(tzinfo=timezone.utc)
    if isinstance(updated_at_raw, datetime):
        updated_at = updated_at_raw if updated_at_raw.tzinfo else updated_at_raw.replace(tzinfo=timezone.utc)

    migrated = UserPlan(
        id=str(doc.get("_id")) if doc.get("_id") else None,
        schema_version="plan_v2",
        plan_status="active",
        user_email=user_email,
        title=str(doc.get("title") or "Plano migrado"),
        goal=goal,
        timeline=timeline,
        user_context=user_context,
        training=training_payload,
        nutrition=nutrition,
        alignment=alignment,
        tracking=tracking,
        latest_review=latest_review,
        review_history=review_history,
        created_from="migration",
        last_material_change_at=updated_at,
        review_reason=str(doc.get("change_reason")) if doc.get("change_reason") else "migration_legacy_plan",
        data_confidence="medium",
        created_at=created_at,
        updated_at=updated_at,
    )
    report = {
        "warnings": warnings,
        "schedule_actions": schedule_actions,
    }
    return migrated, report


def _build_client(uri: str) -> MongoClient:
    return MongoClient(uri, serverSelectionTimeoutMS=10000)


def _backup_docs(docs: list[dict[str, Any]], backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    with backup_path.open("w", encoding="utf-8") as handle:
        for doc in docs:
            payload = {
                "_id": str(doc.get("_id")),
                "user_email": doc.get("user_email"),
                "document": json.loads(json.dumps(doc, default=str)),
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _collect_documents(collection: Collection, email: str | None) -> list[dict[str, Any]]:
    query: dict[str, Any] = {}
    if email:
        query["user_email"] = email.lower().strip()
    return list(collection.find(query))


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate legacy plans to plan_v2.")
    parser.add_argument("--email", help="Optional single user_email scope")
    parser.add_argument("--mongo-uri", default=settings.MONGO_URI, help="Mongo connection URI")
    parser.add_argument("--db-name", default=settings.DB_NAME, help="Mongo database name")
    parser.add_argument("--mode", choices=("dry-run", "write"), default="dry-run")
    parser.add_argument("--backup-file", help="Optional backup jsonl file path")
    args = parser.parse_args()

    client = _build_client(args.mongo_uri)
    db = client[args.db_name]
    plans = db["plans"]
    docs = _collect_documents(plans, args.email)
    if not docs:
        print("No documents found for scope.")
        return

    backup_file = (
        Path(args.backup_file)
        if args.backup_file
        else Path("artifacts") / "plan_migrations" / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-plans-backup.jsonl"
    )

    results: list[MigrationResult] = []
    migrated_docs: list[tuple[dict[str, Any], UserPlan, dict[str, Any]]] = []
    for doc in docs:
        user_email = str(doc.get("user_email") or "<missing>")
        schema_before = str(doc.get("schema_version") or "<missing>")
        if schema_before == "plan_v2":
            results.append(
                MigrationResult(
                    user_email=user_email,
                    schema_before=schema_before,
                    status="skipped_already_v2",
                    warnings=[],
                    errors=[],
                )
            )
            continue
        try:
            migrated, report = migrate_legacy_doc(doc)
            migrated_docs.append((doc, migrated, report))
            results.append(
                MigrationResult(
                    user_email=user_email,
                    schema_before=schema_before,
                    status="ready",
                    warnings=report["warnings"],
                    errors=[],
                )
            )
        except (ValidationError, ValueError, TypeError) as exc:
            results.append(
                MigrationResult(
                    user_email=user_email,
                    schema_before=schema_before,
                    status="failed",
                    warnings=[],
                    errors=[str(exc)],
                )
            )

    has_failures = any(r.status == "failed" for r in results)
    for result in results:
        print(
            json.dumps(
                {
                    "user_email": result.user_email,
                    "schema_before": result.schema_before,
                    "status": result.status,
                    "warnings": result.warnings,
                    "errors": result.errors,
                },
                ensure_ascii=False,
            )
        )

    if args.mode == "dry-run":
        print(f"Dry-run complete. docs={len(docs)} failures={sum(1 for r in results if r.status == 'failed')}")
        return

    if has_failures:
        raise RuntimeError("write mode blocked: dry-run validation failures detected")

    _backup_docs([doc for doc, _, _ in migrated_docs], backup_file)
    print(f"Backup written: {backup_file}")

    for original_doc, migrated_model, _report in migrated_docs:
        payload = migrated_model.model_dump(mode="json", exclude={"id"})
        plans.replace_one({"_id": original_doc["_id"]}, payload, upsert=False)
        reloaded = plans.find_one({"_id": original_doc["_id"]})
        if not reloaded:
            raise RuntimeError(f"post-write read failed for user {migrated_model.user_email}")
        UserPlan(**reloaded)

    print(f"Write complete. migrated={len(migrated_docs)}")


if __name__ == "__main__":
    main()
