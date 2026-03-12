"""
Dashboard endpoints for aggregating user data.
"""

from datetime import datetime, timedelta
from typing import Annotated, List, Any

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


def _get_metabolism_stats(db: MongoDatabase, user_email: str) -> MetabolismStats:
    """Metabolism section of dashboard."""
    tdee_service = AdaptiveTDEEService(db)
    tdee_data = tdee_service.calculate_tdee(user_email, lookback_weeks=3)

    return MetabolismStats(
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


def _get_calorie_stats(
    db: MongoDatabase, user_email: str, today: datetime, daily_target: int
) -> CalorieStats:
    """Calorie section of dashboard."""
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    todays_nut = db.get_nutrition_logs_by_date_range(user_email, start, end)
    total_cal = sum(log.calories for log in todays_nut)
    percent = (total_cal / daily_target * 100) if daily_target > 0 else 0
    return CalorieStats(consumed=total_cal, target=daily_target, percent=round(percent, 1))


def _get_workout_analytics(
    db: MongoDatabase, user_email: str, today: datetime, recent_workouts: list
) -> dict[str, Any]:
    """Workout analytics section."""
    summary = _calculate_workout_summary(today, recent_workouts)
    w_stats = WorkoutStats(
        completed=summary["count"], target=4, lastWorkoutDate=summary["last_date"]
    )

    workout_repo = WorkoutRepository(db.database)
    analytics = workout_repo.get_stats(user_email)

    last_workout = getattr(analytics, "last_workout", None)
    streak = StreakStats(
        current_weeks=analytics.current_streak_weeks,
        current_days=0,
        last_activity_date=str(last_workout.date) if last_workout else None,
    )

    prs = [
        PRRecord(
            id=f"{pr.workout_id}_{pr.exercise_name}",
            exercise=pr.exercise_name,
            weight=pr.weight,
            reps=pr.reps,
            date=str(pr.date),
            previous_weight=None,
        )
        for pr in analytics.recent_prs
    ]

    radar_data = None
    if analytics.strength_radar:
        radar_dict = getattr(analytics, "strength_radar", {})
        radar_data = StrengthRadarData(
            push=radar_dict.get("Push", 0.0),
            pull=radar_dict.get("Pull", 0.0),
            legs=radar_dict.get("Legs", 0.0),
            core=radar_dict.get("Core", 0.0),
        )

    return {
        "w_stats": w_stats,
        "streak": streak,
        "prs": prs,
        "radar": radar_data,
        "analytics": analytics
    }


def _get_composition_trends(
    tdee_service: AdaptiveTDEEService, logs: list
) -> dict[str, list[TrendPoint]]:
    """Composition trends (Weight/Fat/Muscle)."""
    logs_asc = sorted(logs, key=lambda x: x.date)

    w_trend = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.trend_weight if log.trend_weight is not None else log.weight_kg,
        )
        for log in logs_asc
    ]

    fat_hist = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.body_fat_pct,
        )
        for log in logs_asc if log.body_fat_pct is not None
    ]

    fat_trend = []
    ema_fat = None
    for log in logs_asc:
        if log.body_fat_pct is not None:
            ema_fat = tdee_service.calculate_ema_trend(log.body_fat_pct, ema_fat)
            fat_trend.append(TrendPoint(
                date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
                value=ema_fat,
            ))

    mus_hist = [
        TrendPoint(
            date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
            value=log.muscle_mass_pct,
        )
        for log in logs_asc if log.muscle_mass_pct is not None
    ]

    mus_trend = []
    ema_mus = None
    for log in logs_asc:
        if log.muscle_mass_pct is not None:
            ema_mus = tdee_service.calculate_ema_trend(log.muscle_mass_pct, ema_mus)
            mus_trend.append(TrendPoint(
                date=log.date.isoformat() if isinstance(log.date, datetime) else str(log.date),
                value=ema_mus,
            ))

    return {
        "w_trend": w_trend,
        "fat_hist": fat_hist,
        "fat_trend": fat_trend,
        "mus_hist": mus_hist,
        "mus_trend": mus_trend
    }


@router.get("", response_model=DashboardData)
def get_dashboard_data(user_email: CurrentUser, db: DatabaseDep) -> DashboardData:
    """Aggregates data for the user's dashboard."""
    today = _get_today()
    weight_logs = db.get_weight_logs(user_email, limit=30)
    body_stats = _calculate_body_stats(today, weight_logs)

    metab_stats = _get_metabolism_stats(db, user_email)
    cal_stats = _get_calorie_stats(db, user_email, today, metab_stats.daily_target)

    recent_w = db.get_workout_logs(user_email, limit=30)
    w_data = _get_workout_analytics(db, user_email, today, recent_w)
    c_data = _get_composition_trends(AdaptiveTDEEService(db), weight_logs)

    activities = _assemble_recent_activities(
        recent_w, db.get_nutrition_logs(user_email, limit=10), weight_logs
    )

    weight_hist = [
        WeightHistoryPoint(
            date=str(log.date.date() if isinstance(log.date, datetime) else log.date),
            weight=log.weight_kg
        ) for log in reversed(weight_logs)
    ]

    return DashboardData(
        stats=DashboardStats(
            metabolism=metab_stats, body=body_stats,
            calories=cal_stats, workouts=w_data["w_stats"]
        ),
        recentActivities=activities[:5],
        weightHistory=weight_hist,
        weightTrend=c_data["w_trend"],
        fatHistory=c_data["fat_hist"],
        fatTrend=c_data["fat_trend"],
        muscleHistory=c_data["mus_hist"],
        muscleTrend=c_data["mus_trend"],
        streak=w_data["streak"],
        recentPRs=w_data["prs"],
        strengthRadar=w_data["radar"],
        volumeTrend=w_data["analytics"].volume_trend,
        weeklyFrequency=w_data["analytics"].weekly_frequency,
    )


def _get_latest_metrics(weight_logs: list) -> tuple:
    """Extracts latest weight, fat, muscle and bmr."""
    if not weight_logs:
        return 0.0, None, None, None, None

    latest_log = weight_logs[0]
    curr_w = latest_log.weight_kg
    fat = next(
        (log.body_fat_pct for log in weight_logs if log.body_fat_pct is not None), None
    )
    mus_pct = next(
        (log.muscle_mass_pct for log in weight_logs if log.muscle_mass_pct is not None),
        None,
    )
    mus_kg = next(
        (log.muscle_mass_kg for log in weight_logs if log.muscle_mass_kg is not None),
        None,
    )
    bmr = next((log.bmr for log in weight_logs if log.bmr is not None), None)
    return curr_w, fat, mus_pct, mus_kg, bmr


def _find_closest_logs(today: datetime, weight_logs: list) -> dict:
    """Finds logs closest to 7, 15, and 30 days ago."""
    target_dates = {
        7: today.date() - timedelta(days=7),
        15: today.date() - timedelta(days=15),
        30: today.date() - timedelta(days=30),
    }
    closest_logs = {7: None, 15: None, 30: None}
    min_diffs = {7: 999, 15: 999, 30: 999}

    for log in weight_logs[1:]:
        l_date = log.date.date() if isinstance(log.date, datetime) else log.date
        for p in [7, 15, 30]:
            diff = abs((l_date - target_dates[p]).days)
            thresh = 3 if p == 7 else 5
            if diff < min_diffs[p] and diff <= thresh:
                closest_logs[p] = log
                min_diffs[p] = diff
    return closest_logs


def _calculate_body_stats(today: datetime, weight_logs: List[Any]) -> BodyStats:
    """Helper to calculate body stats and trends."""
    curr_w, fat_pct, mus_pct, mus_kg, bmr = _get_latest_metrics(weight_logs)

    diffs: dict[str, Any] = {
        "w": [0.0, None, None], "f": [None, None, None], "m": [None, None, None]
    }
    trend = "stable"

    if weight_logs:
        closest = _find_closest_logs(today, weight_logs)
        for i, period in enumerate([7, 15, 30]):
            cl = closest.get(period)
            if cl:
                diffs["w"][i] = round(curr_w - cl.weight_kg, 2) if i > 0 else curr_w - cl.weight_kg
                if fat_pct is not None and cl.body_fat_pct is not None:
                    diffs["f"][i] = round(fat_pct - cl.body_fat_pct, 1)
                if mus_pct is not None and cl.muscle_mass_pct is not None:
                    diffs["m"][i] = round(mus_pct - cl.muscle_mass_pct, 1)

        if diffs["w"][0] > 0.3:
            trend = "up"
        elif diffs["w"][0] < -0.3:
            trend = "down"

    return BodyStats(
        weight_current=curr_w, weight_diff=round(diffs["w"][0], 2),
        weight_diff_15=diffs["w"][1], weight_diff_30=diffs["w"][2], weight_trend=trend,
        body_fat_pct=fat_pct, muscle_mass_pct=mus_pct, muscle_mass_kg=mus_kg,
        fat_diff=diffs["f"][0], fat_diff_15=diffs["f"][1], fat_diff_30=diffs["f"][2],
        muscle_diff=diffs["m"][0], muscle_diff_15=diffs["m"][1], muscle_diff_30=diffs["m"][2],
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
            except (ValueError, TypeError, KeyError):
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

    activities.sort(key=lambda x: datetime.strptime(x.date, "%d/%m/%Y"), reverse=True)
    return activities
