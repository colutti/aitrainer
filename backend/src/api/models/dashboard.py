from pydantic import BaseModel
from typing import List, Literal, Optional, Dict

class CalorieStats(BaseModel):
    consumed: float
    target: float
    percent: float

class WorkoutStats(BaseModel):
    completed: int
    target: int
    lastWorkoutDate: Optional[str] = None

class BodyStats(BaseModel):
    weight_current: float
    weight_diff: float
    weight_trend: Literal['up', 'down', 'stable']
    body_fat_pct: Optional[float] = None
    muscle_mass_pct: Optional[float] = None
    bmr: Optional[float] = None

class MetabolismStats(BaseModel):
    tdee: int
    daily_target: int
    confidence: str
    weekly_change: float = 0.0
    energy_balance: float = 0.0
    status: str
    macro_targets: Optional[Dict[str, int]] = None
    goal_type: str = "maintain"
    consistency_score: int = 0

class DashboardStats(BaseModel):
    metabolism: MetabolismStats
    body: BodyStats
    calories: CalorieStats
    workouts: WorkoutStats

class RecentActivity(BaseModel):
    id: str
    type: Literal['workout', 'nutrition', 'body']
    title: str
    subtitle: str
    date: str
    icon: Optional[str] = None


class WeightHistoryPoint(BaseModel):
    date: str
    weight: float

class StreakStats(BaseModel):
    current_weeks: int
    current_days: int
    last_activity_date: Optional[str] = None

class PRRecord(BaseModel):
    id: str
    exercise: str
    weight: float
    reps: int
    date: str
    previous_weight: Optional[float] = None

class StrengthRadarData(BaseModel):
    push: float
    pull: float
    legs: float
    core: Optional[float] = None

class DashboardData(BaseModel):
    stats: DashboardStats
    recentActivities: List[RecentActivity]
    weightHistory: Optional[List[WeightHistoryPoint]] = None
    streak: Optional[StreakStats] = None
    recentPRs: Optional[List[PRRecord]] = None
    strengthRadar: Optional[StrengthRadarData] = None
    volumeTrend: Optional[List[float]] = None
    weeklyFrequency: Optional[List[bool]] = None
