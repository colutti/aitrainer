"""
This module contains the models for the user's dashboard data.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel


class CalorieStats(BaseModel):
    """Stats for calorie consumption."""

    consumed: float
    target: float
    percent: float


class WorkoutStats(BaseModel):
    """Stats for user's workouts."""

    completed: int
    target: int
    lastWorkoutDate: Optional[str] = None


class BodyStats(BaseModel):
    """Stats for user's body composition."""

    weight_current: float
    weight_diff: float
    weight_diff_15: Optional[float] = None
    weight_diff_30: Optional[float] = None
    weight_trend: Literal["up", "down", "stable"]
    body_fat_pct: Optional[float] = None
    muscle_mass_pct: Optional[float] = None
    fat_diff: Optional[float] = None
    fat_diff_15: Optional[float] = None
    fat_diff_30: Optional[float] = None
    muscle_diff: Optional[float] = None
    muscle_diff_15: Optional[float] = None
    muscle_diff_30: Optional[float] = None
    bmr: Optional[float] = None


class MetabolismStats(BaseModel):
    """Stats for user's metabolism."""

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
    """Aggregated stats for the dashboard."""

    metabolism: MetabolismStats
    body: BodyStats
    calories: CalorieStats
    workouts: WorkoutStats


class RecentActivity(BaseModel):
    """Model for a recent activity entry."""

    id: str
    type: Literal["workout", "nutrition", "body"]
    title: str
    subtitle: str
    date: str
    icon: Optional[str] = None


class WeightHistoryPoint(BaseModel):
    """Model for a point in the weight history graph."""

    date: str
    weight: float


class TrendPoint(BaseModel):
    """Model for a trend data point (generic for weight, fat, muscle, etc)."""

    date: str
    value: float


class StreakStats(BaseModel):
    """Stats for user's activity streak."""

    current_weeks: int
    current_days: int
    last_activity_date: Optional[str] = None


class PRRecord(BaseModel):
    """Model for a Personal Record entry."""

    id: str
    exercise: str
    weight: float
    reps: int
    date: str
    previous_weight: Optional[float] = None


class StrengthRadarData(BaseModel):
    """Model for strength distribution data."""

    push: float
    pull: float
    legs: float
    core: Optional[float] = None


class DashboardData(BaseModel):
    """The full data structure returned to the dashboard."""

    stats: DashboardStats
    recentActivities: List[RecentActivity]
    weightHistory: Optional[List[WeightHistoryPoint]] = None
    weightTrend: Optional[List[TrendPoint]] = None
    fatTrend: Optional[List[TrendPoint]] = None
    muscleTrend: Optional[List[TrendPoint]] = None
    streak: Optional[StreakStats] = None
    recentPRs: Optional[List[PRRecord]] = None
    strengthRadar: Optional[StrengthRadarData] = None
    volumeTrend: Optional[List[float]] = None
    weeklyFrequency: Optional[List[bool]] = None
