from datetime import datetime, timedelta
from typing import Annotated, List

from fastapi import APIRouter, Depends
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.services.adaptive_tdee import AdaptiveTDEEService
from src.repositories.workout_repository import WorkoutRepository
from src.api.models.dashboard import (
    DashboardData, DashboardStats, RecentActivity, BodyStats, CalorieStats, 
    WorkoutStats, MetabolismStats, WeightHistoryPoint, StreakStats, PRRecord, StrengthRadarData
)

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
DatabaseDep = Annotated[MongoDatabase, Depends(get_mongo_database)]

@router.get("", response_model=DashboardData)
def get_dashboard_data(user_email: CurrentUser, db: DatabaseDep) -> DashboardData:
    """
    Aggregates data for the user's dashboard.
    """
    today = datetime.now()
    start_of_today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_today = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # --- Body Stats (Weight & Composition) ---
    # Fetch logs
    weight_logs = db.get_weight_logs(user_email, limit=14) # Get enough history for trend
    
    current_weight = 0.0
    weight_diff_week = 0.0
    weight_trend = 'stable'
    body_fat_pct = None
    muscle_mass_pct = None
    bmr = None
    
    if weight_logs:
        # Latest Log Stats
        latest_log = weight_logs[0]
        current_weight = latest_log.weight_kg
        
        # Persistence Logic: Find the most recent non-null value for composition fields
        body_fat_pct = next((log.body_fat_pct for log in weight_logs if log.body_fat_pct is not None), None)
        muscle_mass_pct = next((log.muscle_mass_pct for log in weight_logs if log.muscle_mass_pct is not None), None)
        bmr = next((log.bmr for log in weight_logs if log.bmr is not None), None)

        # Calculate Weekly Variation
        # Find log closest to 7 days ago
        target_date = today.date() - timedelta(days=7)
        closest_log = None
        min_days_diff = 999
        
        for log in weight_logs[1:]: # Skip latest
            # Ensure log.date is date object
            log_date = log.date if isinstance(log.date, datetime) else log.date # It might be a date object
            # If log.date is datetime, convert to date
            if isinstance(log_date, datetime):
                log_date = log_date.date()
                
            days_diff = abs((log_date - target_date).days)
            if days_diff < min_days_diff and days_diff <= 3: # Only reasonable window
                closest_log = log
                min_days_diff = days_diff
        
        if closest_log:
            weight_diff_week = current_weight - closest_log.weight_kg
        
        # Determine trend label
        if weight_diff_week > 0.3:
            weight_trend = 'up'
        elif weight_diff_week < -0.3:
            weight_trend = 'down'
        else:
            weight_trend = 'stable'

    body_stats = BodyStats(
        weight_current=current_weight,
        weight_diff=round(weight_diff_week, 2),
        weight_trend=weight_trend,
        body_fat_pct=body_fat_pct,
        muscle_mass_pct=muscle_mass_pct,
        bmr=bmr
    )

    # --- Calorie Stats (Synced with Metabolism) ---
    # Fetch today's logs
    todays_nutrition = db.get_nutrition_logs_by_date_range(user_email, start_of_today, end_of_today)
    total_calories = sum(log.calories for log in todays_nutrition)
    
    # --- Metabolism & TDEE Stats ---
    # Centralize TDEE calculation to ensure consistency across widgets
    tdee_service = AdaptiveTDEEService(db)
    
    # Calculate with default 3 weeks lookback
    tdee_data = tdee_service.calculate_tdee(user_email, lookback_weeks=3)
    
    metabolism_stats = MetabolismStats(
        tdee=tdee_data.get('tdee', 0),
        daily_target=tdee_data.get('daily_target', 2000),
        confidence=tdee_data.get('confidence', 'none'),
        weekly_change=tdee_data.get('weight_change_per_week', 0.0),
        energy_balance=tdee_data.get('energy_balance', 0.0),
        status=tdee_data.get('status', 'maintenance'),
        macro_targets=tdee_data.get('macro_targets'),
        goal_type=tdee_data.get('goal_type', 'maintain'),
        consistency_score=tdee_data.get('consistency_score', 0)
    )

    # --- Calorie Stats ---
    # Use the calculated target from TDEE service
    calorie_target = metabolism_stats.daily_target
    calorie_percent = (total_calories / calorie_target) * 100 if calorie_target > 0 else 0
    
    calorie_stats = CalorieStats(
        consumed=total_calories,
        target=calorie_target,
        percent=round(calorie_percent, 1)
    )

    # --- Workout Stats ---
    recent_workouts = db.get_workout_logs(user_email, limit=30)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    
    workouts_this_week = 0
    last_workout_date = None
    
    if recent_workouts:
        last_workout_date = recent_workouts[0].date # Keep as is (string/datetime)
        
        for w in recent_workouts:
            try:
                # If date is string, parse it
                w_date = w.date
                if isinstance(w_date, str):
                    w_date = datetime.fromisoformat(w_date.replace('Z', '+00:00'))
                
                # Check if naive or aware.
                if w_date.tzinfo and start_of_week.tzinfo is None:
                    w_date = w_date.replace(tzinfo=None)
                
                if w_date >= start_of_week:
                    workouts_this_week += 1
            except Exception:
                pass
    
    # --- Extended Workout Analytics (Streak, PRs, Radar) ---
    workout_repo = WorkoutRepository(db.database)
    workout_analytics = workout_repo.get_stats(user_email)
    
    # 1. Streak
    streak_data = StreakStats(
        current_weeks=workout_analytics.current_streak_weeks,
        current_days=0, # Days streak not yet implemented in repo, placeholder
        last_activity_date=str(workout_analytics.last_workout.date) if workout_analytics.last_workout else None
    )

    # 2. Recent PRs
    recent_prs_data: List[PRRecord] = []
    for pr in workout_analytics.recent_prs:
        recent_prs_data.append(PRRecord(
            id=f"{pr.workout_id}_{pr.exercise_name}",
            exercise=pr.exercise_name,
            weight=pr.weight,
            reps=pr.reps,
            date=str(pr.date),
            previous_weight=None # Not yet implemented in repo
        ))

    # 3. Strength Radar
    # Map repo output to StrengthRadarData
    radar_data = None
    if workout_analytics.strength_radar:
        radar_data = StrengthRadarData(
            push=workout_analytics.strength_radar.get('Push', 0.0),
            pull=workout_analytics.strength_radar.get('Pull', 0.0),
            legs=workout_analytics.strength_radar.get('Legs', 0.0),
            core=workout_analytics.strength_radar.get('Core', 0.0)
        )
    
    # --- Weight History ---
    # Map weight_logs (limit=14 above) to WeightHistoryPoint
    # We might want to fetch more history for the chart, e.g. 30 days
    # Let's use the existing logs for now as 14 days is a decent start
    weight_history_data: List[WeightHistoryPoint] = []
    # Reverse to have oldest first for chart
    for log in reversed(weight_logs):
        weight_history_data.append(WeightHistoryPoint(
            date=str(log.date.date() if isinstance(log.date, datetime) else log.date),
            weight=log.weight_kg
        ))

    # Get weekly goal from UserProfile (if available, defaulting to 4)
    _ = db.get_user_profile(user_email)
    # Field workouts_per_week is currently missing in UserProfile model, defaulting to 4
    workout_target = 4


    workout_stats = WorkoutStats(
        completed=workouts_this_week,
        target=workout_target,
        lastWorkoutDate=str(last_workout_date) if last_workout_date else None
    )

    # --- Recent Activities ---
    activities: List[RecentActivity] = []
    
    # 1. Workouts (Top 3 unique)
    seen_workout_ids = set()
    workout_count = 0
    for w in recent_workouts:
        if w.id in seen_workout_ids:
            continue
        seen_workout_ids.add(w.id)
        
        activities.append(RecentActivity(
            id=w.id,
            type='workout',
            title=f"Treino de {w.workout_type or 'Força'}",
            subtitle=f"{w.duration_minutes or 0} min • {len(w.exercises)} exercícios",
            date=str(w.date),
            icon='dumbbell'
        ))
        workout_count += 1
        if workout_count >= 3:
            break
            
    # 2. Nutrition (Recent 5)
    recent_nutrition = db.get_nutrition_logs(user_email, limit=10)
    for n in recent_nutrition:
        # Use _id if available, otherwise date
        n_id = getattr(n, 'id', str(n.date))
        activities.append(RecentActivity(
            id=str(n_id),
            type='nutrition',
            title="Refeição Registrada",
            subtitle=f"{n.calories} kcal • {n.protein_grams}g proteína",
            date=str(n.date),
            icon='utensils'
        ))
        if len([a for a in activities if a.type == 'nutrition']) >= 5:
            break
        
    # 3. Weight (Top 2)
    for weight in weight_logs[:2]:
        activities.append(RecentActivity(
            id=str(weight.date),
            type='body',
            title="Pesagem",
            subtitle=f"{weight.weight_kg} kg",
            date=str(weight.date),
            icon='scale'
        ))

    # Sort combined activities by date desc
    activities.sort(key=lambda x: str(x.date), reverse=True)
    
    return DashboardData(
        stats=DashboardStats(
            metabolism=metabolism_stats,
            body=body_stats,
            calories=calorie_stats,
            workouts=workout_stats
        ),
        recentActivities=activities[:5], # Return top 5
        weightHistory=weight_history_data,
        streak=streak_data,
        recentPRs=recent_prs_data,
        strengthRadar=radar_data,
        volumeTrend=workout_analytics.volume_trend,
        weeklyFrequency=workout_analytics.weekly_frequency
    )
