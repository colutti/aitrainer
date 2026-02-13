"""
Dashboard endpoints for aggregating user data.
"""

# pylint: disable=no-member,broad-exception-caught
from datetime import datetime, timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.repositories.workout_repository import WorkoutRepository
from src.api.models.dashboard import (
    DashboardData,
    DashboardStats,
    RecentActivity,
    BodyStats,
    CalorieStats,
    WorkoutStats,
    MetabolismStats,
    WeightHistoryPoint,
    TrendPoint,
    StreakStats,
    PRRecord,
    StrengthRadarData,
)

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.get("", response_model=DashboardData)
# pylint: disable=too-many-locals
def get_dashboard_data(
    user_email: CurrentUser,
    db: DatabaseDep,
) -> DashboardData:
    """
    Aggregates data for the user's dashboard.
    """
    # user_email is passed directly
    today = datetime.now()

    # --- Body Stats ---
    weight_logs = db.get_weight_logs(user_email, limit=14)
    body_stats = _calculate_body_stats(today, weight_logs)

    # --- Metabolism & TDEE Stats ---
    tdee_service = AdaptiveTDEEService(db)
    tdee_data = tdee_service.calculate_tdee(user_email, lookback_weeks=3)

    metabolism_stats = MetabolismStats(
        tdee=tdee_data.get("tdee", 0),
        daily_target=tdee_data.get("daily_target", 2000),
        confidence=tdee_data.get("confidence", "none"),
        weekly_change=tdee_data.get("weight_change_per_week", 0.0),
        energy_balance=tdee_data.get("energy_balance", 0.0),
        status=tdee_data.get("status", "maintenance"),
        macro_targets=tdee_data.get("macro_targets"),
        goal_type=tdee_data.get("goal_type", "maintain"),
        consistency_score=tdee_data.get("consistency_score", 0),
    )

    # --- Calorie Stats ---
    start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    todays_nutrition = db.get_nutrition_logs_by_date_range(
        user_email, start_of_today, end_of_today
    )
    total_calories = sum(log.calories for log in todays_nutrition)
    calorie_target = metabolism_stats.daily_target
    calorie_percent = (total_calories / calorie_target * 100) if calorie_target > 0 else 0

    calorie_stats = CalorieStats(
        consumed=total_calories,
        target=calorie_target,
        percent=round(calorie_percent, 1),
    )

    # --- Workout Stats ---
    recent_workouts = db.get_workout_logs(user_email, limit=30)
    workout_summary = _calculate_workout_summary(today, recent_workouts)

    workout_stats = WorkoutStats(
        completed=workout_summary["count"],
        target=4,  # Default target
        lastWorkoutDate=workout_summary["last_date"],
    )

    # --- Extended Workout Analytics ---
    workout_repo = WorkoutRepository(db.database)
    workout_analytics = workout_repo.get_stats(user_email)

    streak_data = StreakStats(
        current_weeks=workout_analytics.current_streak_weeks,
        current_days=0,
        last_activity_date=str(workout_analytics.last_workout.date)
        if workout_analytics.last_workout
        else None,
    )

    recent_prs_data = [
        PRRecord(
            id=f"{pr.workout_id}_{pr.exercise_name}",
            exercise=pr.exercise_name,
            weight=pr.weight,
            reps=pr.reps,
            date=str(pr.date),
            previous_weight=None,
        )
        for pr in workout_analytics.recent_prs
    ]

    radar_data = None
    if workout_analytics.strength_radar:
        radar_data = StrengthRadarData(
            push=workout_analytics.strength_radar.get("Push", 0.0),
            pull=workout_analytics.strength_radar.get("Pull", 0.0),
            legs=workout_analytics.strength_radar.get("Legs", 0.0),
            core=workout_analytics.strength_radar.get("Core", 0.0),
        )

    # --- Weight History ---
    weight_history_data = [
        WeightHistoryPoint(
            date=str(log.date.date() if isinstance(log.date, datetime) else log.date),
            weight=log.weight_kg,
        )
        for log in reversed(weight_logs)
    ]

    # --- Composition Trends (30 days) ---
    composition_logs = db.get_weight_logs(user_email, limit=30)
    composition_logs_asc = sorted(composition_logs, key=lambda x: x.date)

    weight_trend_data = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.weight_kg,
        )
        for log in composition_logs_asc
    ]

    fat_trend_data = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.body_fat_pct,
        )
        for log in composition_logs_asc
        if log.body_fat_pct is not None
    ]

    muscle_trend_data = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.muscle_mass_pct,
        )
        for log in composition_logs_asc
        if log.muscle_mass_pct is not None
    ]

    # --- Recent Activities ---
    activities = _assemble_recent_activities(
        recent_workouts,
        db.get_nutrition_logs(user_email, limit=10),
        weight_logs,
    )

    return DashboardData(
        stats=DashboardStats(
            metabolism=metabolism_stats,
            body=body_stats,
            calories=calorie_stats,
            workouts=workout_stats,
        ),
        recentActivities=activities[:5],
        weightHistory=weight_history_data,
        weightTrend=weight_trend_data,
        fatTrend=fat_trend_data,
        muscleTrend=muscle_trend_data,
        streak=streak_data,
        recentPRs=recent_prs_data,
        strengthRadar=radar_data,
        volumeTrend=workout_analytics.volume_trend,
        weeklyFrequency=workout_analytics.weekly_frequency,
    )


def _calculate_body_stats(today, weight_logs) -> BodyStats:
    """Helper to calculate body stats and trends."""
    current_weight = 0.0
    weight_diff_week = 0.0
    weight_trend = "stable"
    body_fat_pct = None
    muscle_mass_pct = None
    bmr = None

    if weight_logs:
        latest_log = weight_logs[0]
        current_weight = latest_log.weight_kg
        body_fat_pct = next(
            (log.body_fat_pct for log in weight_logs if log.body_fat_pct is not None),
            None,
        )
        muscle_mass_pct = next(
            (log.muscle_mass_pct for log in weight_logs if log.muscle_mass_pct is not None),
            None,
        )
        bmr = next((log.bmr for log in weight_logs if log.bmr is not None), None)

        target_date = today.date() - timedelta(days=7)
        closest_log = None
        min_days_diff = 999

        for log in weight_logs[1:]:
            log_date = log.date.date() if isinstance(log.date, datetime) else log.date
            days_diff = abs((log_date - target_date).days)
            if days_diff < min_days_diff and days_diff <= 3:
                closest_log = log
                min_days_diff = days_diff

        if closest_log:
            weight_diff_week = current_weight - closest_log.weight_kg

        if weight_diff_week > 0.3:
            weight_trend = "up"
        elif weight_diff_week < -0.3:
            weight_trend = "down"

    return BodyStats(
        weight_current=current_weight,
        weight_diff=round(weight_diff_week, 2),
        weight_trend=weight_trend,
        body_fat_pct=body_fat_pct,
        muscle_mass_pct=muscle_mass_pct,
        bmr=bmr,
    )


def _calculate_workout_summary(today, recent_workouts) -> dict:
    """Helper to calculate workout count and last date for current week."""
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)

    count = 0
    last_date = None
    if recent_workouts:
        last_date = str(recent_workouts[0].date)
        for w in recent_workouts:
            try:
                w_date = w.date
                if isinstance(w_date, str):
                    w_date = datetime.fromisoformat(w_date.replace("Z", "+00:00"))
                if w_date.tzinfo and start_of_week.tzinfo is None:
                    w_date = w_date.replace(tzinfo=None)
                if w_date >= start_of_week:
                    count += 1
            except Exception: # pylint: disable=broad-exception-caught
                continue
    return {"count": count, "last_date": last_date}


def _assemble_recent_activities(workouts, nutrition, weight_logs) -> List[RecentActivity]:
    """Helper to assemble and sort recent activities."""
    activities: List[RecentActivity] = []

    # Workouts
    seen_ids = set()
    for w in workouts[:5]:
        if w.id not in seen_ids:
            seen_ids.add(w.id)
            activities.append(RecentActivity(
                id=w.id, type="workout", title=f"Treino de {w.workout_type or 'Força'}",
                subtitle=f"{w.duration_minutes or 0} min • {len(w.exercises)} exercícios",
                date=str(w.date), icon="dumbbell"
            ))

    # Nutrition
    for n in nutrition[:5]:
        activities.append(RecentActivity(
            id=str(getattr(n, "id", n.date)), type="nutrition", title="Refeição Registrada",
            subtitle=f"{n.calories} kcal • {n.protein_grams}g proteína",
            date=str(n.date), icon="utensils"
        ))

    # Weight
    for weight in weight_logs[:2]:
        activities.append(RecentActivity(
            id=str(weight.date), type="body", title="Pesagem",
            subtitle=f"{weight.weight_kg} kg", date=str(weight.date), icon="scale"
        ))

    activities.sort(key=lambda x: str(x.date), reverse=True)
    return activities
