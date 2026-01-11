from datetime import date, timedelta, datetime
from typing import List
import statistics

from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.core.logs import logger
from src.services.database import MongoDatabase

class AdaptiveTDEEService:
    """
    Service for calculating Adaptive TDEE based on weight and nutrition history.
    
    Algorithm:
    TDEE = Average_Calories_Consumed - (Weight_Change_kg * 7700 / Days_Elapsed)
    
    Using Exponential Moving Average (EMA) for weight smoothing.
    """
    
    # Constants
    KCAL_PER_KG_FAT = 7700
    MIN_DATA_DAYS = 7  # Minimum days of data required
    SMOOTHING_FACTOR = 0.1 # Alpha for EMA
    
    # Sanity Limits
    MIN_TDEE = 1200
    MAX_TDEE = 5000
    MAX_DAILY_WEIGHT_CHANGE = 1.0 # kg (flag as anomaly if higher)

    def __init__(self, db: MongoDatabase):
        self.db = db

    def calculate_tdee(self, user_email: str, lookback_weeks: int = 3) -> dict:
        """
        Calculates the user's TDEE over the specified lookback period.
        
        Returns:
            dict: {
                "tdee": int,
                "confidence": str (low, medium, high),
                "avg_calories": int,
                "weight_change_per_week": float,
                "logs_count": int,
                "start_weight": float,
                "end_weight": float
            }
        """
        end_date = date.today()
        start_date = end_date - timedelta(weeks=lookback_weeks)
        
        # 1. Fetch Data
        weight_logs = self.db.get_weight_logs_by_date_range(user_email, start_date, end_date)
        nutrition_logs = self.db.get_nutrition_logs_by_date_range(
            user_email, 
            datetime(start_date.year, start_date.month, start_date.day),
            datetime(end_date.year, end_date.month, end_date.day)
        )
        
        if len(weight_logs) < 2 or len(nutrition_logs) < self.MIN_DATA_DAYS:
            logger.info("Insufficient data for TDEE calculation for user %s", user_email)
            return self._insufficient_data_response()
            
        # 2. Process Weight Data (EMA Smoothing)
        # Sort logs by date ascending
        weight_logs.sort(key=lambda x: x.date)
        
        smoothed_weights = self._calculate_ema_weights(weight_logs)
        if not smoothed_weights:
            return self._insufficient_data_response()

        start_weight = smoothed_weights[0]["weight"]
        end_weight = smoothed_weights[-1]["weight"]
        
        # Effective days = days between first and last weight log
        days_elapsed = (smoothed_weights[-1]["date"] - smoothed_weights[0]["date"]).days
        
        if days_elapsed < self.MIN_DATA_DAYS:
             return self._insufficient_data_response()
             
        # 3. Process Nutrition Data
        # Calculate average daily calories over the exact period covered by weight logs
        # Filter nutrition logs to be within the weight log range
        period_start = smoothed_weights[0]["date"]
        period_end = smoothed_weights[-1]["date"]
        
        # Convert nutrition log dates to date objects for comparison
        relevant_nutrition = [
            l for l in nutrition_logs 
            if period_start <= l.date.date() <= period_end
        ]
        
        if not relevant_nutrition:
             return self._insufficient_data_response()

        total_calories = sum(l.calories for l in relevant_nutrition)
        # Average calories should be over the DAYS ELAPSED, assuming missing logs = typical eating?
        # NO. If they missed logs, we don't know what they ate.
        # Strict approach: Average of LOGGED days. 
        # But TDEE formula tries to balance total energy.
        # If user logs 3000 kcal for 1 day and nothing for 6 days, and maintains weight, 
        # Average intake = 3000? No, probably 3000/7.
        # Assumption: User must log strictly for accurate TDEE.
        # We will use Total Calories / Number of Logs. 
        # AND we check adherence. If adherence is low, confidence is low.
        avg_calories_logged = total_calories / len(relevant_nutrition)
        
        # 4. Calculate TDEE
        # Formula: TDEE = Avg_In - (Delta_Weight_kg * 7700 / Days)
        total_weight_change = end_weight - start_weight
        
        # Daily caloric surplus/deficit implied by weight change
        daily_surplus_deficit = (total_weight_change * self.KCAL_PER_KG_FAT) / days_elapsed
        
        tdee = avg_calories_logged - daily_surplus_deficit
        
        # 5. Sanity Checks & Confidence
        tdee = max(self.MIN_TDEE, min(self.MAX_TDEE, tdee))
        
        confidence = self._calculate_confidence(
            days_elapsed, 
            len(weight_logs), 
            len(relevant_nutrition),
            days_elapsed # Expected logs
        )
        
        weekly_change = (total_weight_change / days_elapsed) * 7
        
        # 6. Include Goal & Target Info
        daily_target = int(round(tdee))
        goal_rate = 0.0
        goal_type = "maintain"
        
        profile = self.db.get_user_profile(user_email)
        if profile:
            goal_rate = profile.weekly_rate or 0.0
            goal_type = profile.goal_type
            
            adjustment = 0
            if goal_type == "lose":
                adjustment = -1 * abs(goal_rate) * 1100
            elif goal_type == "gain":
                adjustment = abs(goal_rate) * 1100
            
            daily_target = int(round(tdee + adjustment))
            daily_target = max(1000, daily_target)

        return {
            "tdee": int(round(tdee)),
            "confidence": confidence,
            "avg_calories": int(round(avg_calories_logged)),
            "weight_change_per_week": round(weekly_change, 2),
            "logs_count": len(relevant_nutrition),
            "startDate": period_start.isoformat(),
            "endDate": period_end.isoformat(),
            "start_weight": round(start_weight, 1),
            "end_weight": round(end_weight, 1),
            "daily_target": daily_target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type
        }

    def _calculate_ema_weights(self, logs: List[WeightLog]) -> List[dict]:
        """
        Applies Exponential Moving Average to weight logs.
        Fills gaps? No, we just smooth existing points or map to daily grid.
        Better to map to daily grid filling gaps with previous known weight
        to capture true time elapsed.
        """
        if not logs: return []
        
        # 1. Fill gaps in date range
        start_date = logs[0].date
        end_date = logs[-1].date
        days = (end_date - start_date).days + 1
        
        daily_weights = []
        current_log_idx = 0
        last_known_weight = logs[0].weight_kg
        
        # Map logs to dictionary for easy lookup
        log_map = {l.date: l.weight_kg for l in logs}
        
        current_ema = logs[0].weight_kg
        smoothed_data = []

        for i in range(days):
            d = start_date + timedelta(days=i)
            
            # Get weight for this day
            weight = log_map.get(d)
            
            if weight is None:
                # If missing, use previous EMA? Or skip?
                # Using previous EMA is safer than raw carry-forward for calculation
                # But physically, weight uses carry-forward of raw value usually.
                # Let's use the Raw Carry Forward for the "Measurement" then update EMA.
                weight = last_known_weight
            else:
                # Anomaly check: if raw weight jumps too much (> 1kg from last known), cap it?
                # Simple check:
                if abs(weight - last_known_weight) > self.MAX_DAILY_WEIGHT_CHANGE:
                    # Could be water weight or error. 
                    # Let's trust EMA to smooth it out, but record it.
                    pass
                last_known_weight = weight
            
            # Update EMA
            # EMA_today = (Val_today * alpha) + (EMA_yesterday * (1-alpha))
            current_ema = (weight * self.SMOOTHING_FACTOR) + (current_ema * (1 - self.SMOOTHING_FACTOR))
            
            smoothed_data.append({
                "date": d,
                "weight": current_ema
            })
            
        return smoothed_data

    def _calculate_confidence(self, days_elapsed: int, weight_count: int, nutrition_count: int, expected_logs: int) -> str:
        """
        Determines confidence level based on data density.
        """
        nutrition_adherence = nutrition_count / expected_logs if expected_logs > 0 else 0
        
        if days_elapsed < 14:
            return "low" # Too short period
            
        if nutrition_adherence > 0.85:
            return "high"
        elif nutrition_adherence > 0.6:
            return "medium"
        else:
            return "low"

    def _insufficient_data_response(self) -> dict:
        return {
            "tdee": 0,
            "confidence": "none",
            "reason": "Insufficient data"
        }

    def get_current_targets(self, user_email: str) -> dict:
        """
        Calculates current TDEE and daily calorie target based on user goal.
        """
        # 1. Get TDEE (3 weeks lookback default)
        tdee_stats = self.calculate_tdee(user_email)
        
        tdee = tdee_stats.get("tdee")
        if not tdee or tdee == 0:
             return {
                 "tdee": None,
                 "daily_target": None,
                 "reason": "Insufficient data for TDEE"
             }
             
        # 2. Get User Profile for Goal
        profile = self.db.get_user_profile(user_email)
        if not profile:
             return {
                 "tdee": int(tdee),
                 "daily_target": int(tdee), # Maintenance default
                 "reason": "No profile found"
             }

        # 3. Calculate Target
        # 1kg fat = ~7700 kcal. 
        # Weekly rate (kg) * 7700 / 7 = Daily deficit/surplus needed
        # 1100 kcal daily per 1kg/week
        
        goal_rate = profile.weekly_rate if profile.weekly_rate else 0.0
        # If goal is Lose, rate is negative? Usually stored as positive magnitude in UI?
        # Let's check profile.goal_type
        
        # goal_type: "lose_weight", "gain_muscle", "maintain"
        # weekly_rate: float (kg/week)
        
        adjustment = 0
        if profile.goal_type == "lose":
             adjustment = -1 * abs(goal_rate) * 1100
        elif profile.goal_type == "gain": # or gain_weight
             adjustment = abs(goal_rate) * 1100
        
        daily_target = tdee + adjustment
        
        # Sanity caps
        daily_target = max(1000, daily_target) # Never recommend below 1000
        
        return {
            "tdee": int(tdee),
            "daily_target": int(daily_target),
            "reason": f"Based on TDEE {tdee} and goal {profile.goal_type}"
        }

