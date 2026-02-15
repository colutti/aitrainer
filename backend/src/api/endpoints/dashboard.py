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


def _get_today() -> datetime:
    """Get current datetime. Extracted for easy mocking in tests."""
    return datetime.now()


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
    today = _get_today()

    # --- Body Stats ---
    weight_logs = db.get_weight_logs(user_email, limit=30)
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
    weight_diff_15 = None
    weight_diff_30 = None
    weight_trend = "stable"
    body_fat_pct = None
    muscle_mass_pct = None
    fat_diff = None
    fat_diff_15 = None
    fat_diff_30 = None
    muscle_diff = None
    muscle_diff_15 = None
    muscle_diff_30 = None
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

        # Find closest logs for 7, 15, and 30 day periods
        target_dates = {
            7: today.date() - timedelta(days=7),
            15: today.date() - timedelta(days=15),
            30: today.date() - timedelta(days=30),
        }
        closest_logs = {7: None, 15: None, 30: None}
        min_days_diffs = {7: 999, 15: 999, 30: 999}

        for log in weight_logs[1:]:
            log_date = log.date.date() if isinstance(log.date, datetime) else log.date
            for period in [7, 15, 30]:
                days_diff = abs((log_date - target_dates[period]).days)
                threshold = 3 if period == 7 else 5  # ±3 days for 7d, ±5 days for 15d/30d
                if days_diff < min_days_diffs[period] and days_diff <= threshold:
                    closest_logs[period] = log
                    min_days_diffs[period] = days_diff

        # Calculate diffs for each period
        closest_log_7 = closest_logs[7]
        if closest_log_7:
            weight_diff_week = current_weight - closest_log_7.weight_kg

            # Calculate fat and muscle diffs for 7 days
            if body_fat_pct is not None and closest_log_7.body_fat_pct is not None:
                fat_diff = round(body_fat_pct - closest_log_7.body_fat_pct, 1)

            if muscle_mass_pct is not None and closest_log_7.muscle_mass_pct is not None:
                muscle_diff = round(muscle_mass_pct - closest_log_7.muscle_mass_pct, 1)

        # 15-day diffs
        closest_log_15 = closest_logs[15]
        if closest_log_15:
            weight_diff_15 = round(current_weight - closest_log_15.weight_kg, 2)
            if body_fat_pct is not None and closest_log_15.body_fat_pct is not None:
                fat_diff_15 = round(body_fat_pct - closest_log_15.body_fat_pct, 1)
            if muscle_mass_pct is not None and closest_log_15.muscle_mass_pct is not None:
                muscle_diff_15 = round(muscle_mass_pct - closest_log_15.muscle_mass_pct, 1)

        # 30-day diffs
        closest_log_30 = closest_logs[30]
        if closest_log_30:
            weight_diff_30 = round(current_weight - closest_log_30.weight_kg, 2)
            if body_fat_pct is not None and closest_log_30.body_fat_pct is not None:
                fat_diff_30 = round(body_fat_pct - closest_log_30.body_fat_pct, 1)
            if muscle_mass_pct is not None and closest_log_30.muscle_mass_pct is not None:
                muscle_diff_30 = round(muscle_mass_pct - closest_log_30.muscle_mass_pct, 1)

        if weight_diff_week > 0.3:
            weight_trend = "up"
        elif weight_diff_week < -0.3:
            weight_trend = "down"

    return BodyStats(
        weight_current=current_weight,
        weight_diff=round(weight_diff_week, 2),
        weight_diff_15=weight_diff_15,
        weight_diff_30=weight_diff_30,
        weight_trend=weight_trend,
        body_fat_pct=body_fat_pct,
        muscle_mass_pct=muscle_mass_pct,
        fat_diff=fat_diff,
        fat_diff_15=fat_diff_15,
        fat_diff_30=fat_diff_30,
        muscle_diff=muscle_diff,
        muscle_diff_15=muscle_diff_15,
        muscle_diff_30=muscle_diff_30,
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


def _format_activity_date(date_obj) -> str:
    """Format date as DD/MM/YYYY (Brazilian format, no time)."""
    if isinstance(date_obj, datetime):
        return date_obj.strftime("%d/%m/%Y")
    # date_obj is already a date object
    return date_obj.strftime("%d/%m/%Y")


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
                date=_format_activity_date(w.date), icon="dumbbell"
            ))

    # Nutrition
    for n in nutrition[:5]:
        activities.append(RecentActivity(
            id=str(getattr(n, "id", n.date)), type="nutrition", title="Refeição Registrada",
            subtitle=f"{n.calories} kcal • {n.protein_grams}g proteína",
            date=_format_activity_date(n.date), icon="utensils"
        ))

    # Weight
    for weight in weight_logs[:2]:
        activities.append(RecentActivity(
            id=str(weight.date), type="body", title="Pesagem",
            subtitle=f"{weight.weight_kg} kg", date=_format_activity_date(weight.date), icon="scale"
        ))

    activities.sort(key=lambda x: x.date, reverse=True)
    return activities
