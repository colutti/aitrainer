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
    
    # Regression config
    MIN_DATA_DAYS_FOR_REGRESSION = 10 
    
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
            
        # 2. Process Weight Data (Trend Estimation)
        # Sort logs by date ascending
        weight_logs.sort(key=lambda x: x.date)
        
        # Calculate trend using Linear Regression
        # This is more accurate for detecting TDEE during active loss/gain than EMA
        slope, intercept, r_value = self._calculate_regression_trend(weight_logs)
        
        # Effective days = days between first and last weight log
        days_elapsed = (weight_logs[-1].date - weight_logs[0].date).days
        
        if days_elapsed < self.MIN_DATA_DAYS:
             return self._insufficient_data_response()
             
        # Theoretical weight change based on the trend
        # We use the predicted values from the regression line for start/end points
        # to avoid being fooled by a single noisy day at the endpoints.
        start_weight = intercept
        end_weight = intercept + (slope * days_elapsed)
        total_weight_change = end_weight - start_weight
             
        # 3. Process Nutrition Data
        # Calculate average daily calories over the exact period covered by weight logs
        # Filter nutrition logs to be within the weight log range
        period_start = weight_logs[0].date
        period_end = weight_logs[-1].date
        
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
        # Formula: TDEE = Avg_In - (Slope_kg_per_day * 7700)
        # Note: Slope is kg/day. If losing, slope is negative. 
        # TDEE = Avg_In - (Negative * 7700) = Avg_In + Positive
        daily_surplus_deficit = slope * self.KCAL_PER_KG_FAT
        
        tdee = avg_calories_logged - daily_surplus_deficit
        
        # 5. Sanity Checks & Confidence
        tdee = max(self.MIN_TDEE, min(self.MAX_TDEE, tdee))
        
        # Energy balance (Negative = Deficit, Positive = Surplus)
        energy_balance = avg_calories_logged - tdee
        
        # Semantic Status
        status = "maintenance"
        if energy_balance < -150:
            status = "deficit"
        elif energy_balance > 150:
            status = "surplus"
            
        is_stable = abs(energy_balance) < 150
        
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

        # 7. Body Composition Analysis
        comp_changes = self._calculate_body_composition_changes(weight_logs)

        result = {
            "tdee": int(round(tdee)),
            "confidence": confidence,
            "avg_calories": int(round(avg_calories_logged)),
            "weight_change_per_week": round(weekly_change, 2),
            "energy_balance": int(round(energy_balance)),
            "status": status,
            "is_stable": is_stable,
            "logs_count": len(relevant_nutrition),
            "startDate": period_start.isoformat(),
            "endDate": period_end.isoformat(),
            "start_weight": round(start_weight, 1),
            "end_weight": round(end_weight, 1),
            "daily_target": daily_target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type
        }
        
        if comp_changes:
            result.update(comp_changes)

        # Include BMR from scale if available in latest log
        latest_log = weight_logs[-1]
        if latest_log.bmr:
            result["scale_bmr"] = latest_log.bmr
            
        return result

    def _calculate_body_composition_changes(self, logs: List[WeightLog]) -> dict | None:
        """Calculate fat and lean mass changes if composition data is available."""
        # Using raw logs for composition, maybe we should smooth this too?
        # For now, end-point analysis on raw logs is simple enough.
        # Ensure we use logs that actually have the data.
        
        valid_logs = [l for l in logs if l.body_fat_pct is not None]
        if len(valid_logs) < 2:
            return None
        
        first = valid_logs[0]
        last = valid_logs[-1]
        
        # Calculate masses
        fat_mass_start = first.weight_kg * (first.body_fat_pct / 100.0)
        fat_mass_end = last.weight_kg * (last.body_fat_pct / 100.0)
        fat_change = fat_mass_end - fat_mass_start
        
        total_weight_change = last.weight_kg - first.weight_kg
        lean_change = total_weight_change - fat_change
        
        return {
            "fat_change_kg": round(fat_change, 2),
            "lean_change_kg": round(lean_change, 2),
            "start_fat_pct": round(first.body_fat_pct, 1),
            "end_fat_pct": round(last.body_fat_pct, 1)
        }

    def _calculate_regression_trend(self, logs: List[WeightLog]) -> tuple[float, float, float]:
        """
        Calculates the linear regression trend of weight logs.
        Returns (slope, intercept, r_value).
        Slope is kg per day.
        """
        import numpy as np
        
        if not logs:
            return 0.0, 0.0, 0.0
            
        start_date = logs[0].date
        x = [] # Days since start
        y = [] # Weights
        
        for log in logs:
            days = (log.date - start_date).days
            x.append(days)
            y.append(log.weight_kg)
            
        if len(x) < 2:
            return 0.0, y[0], 0.0
            
        # Linear regression: y = mx + c
        # m = slope, c = intercept
        # r_value = correlation coefficient
        try:
            x_arr = np.array(x)
            y_arr = np.array(y)
            m, c = np.polyfit(x_arr, y_arr, 1)
            
            # Simple R approximation (not strictly needed but useful for confidence later)
            correlation_matrix = np.corrcoef(x_arr, y_arr)
            r_value = correlation_matrix[0, 1] if correlation_matrix.shape == (2, 2) else 0.0
            
            return float(m), float(c), float(r_value)
        except Exception as e:
            logger.error("Regression calculation failed: %s", e)
            # Fallback to endpoint delta if regression fails
            days_total = x[-1] - x[0]
            if days_total > 0:
                slope = (y[-1] - y[0]) / days_total
            else:
                slope = 0.0
            return slope, y[0], 0.0

    def _calculate_ema_weights(self, logs: List[WeightLog]) -> List[dict]:
        """
        OBSOLETE: Replaced by Regression for TDEE, but kept for potential UI smoothing.
        Applies Exponential Moving Average to weight logs.
        """
        # (Implementation remains same but we use 0.1 alpha)
        alpha = 0.1
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
            "status": tdee_stats.get("status", "maintenance"),
            "energy_balance": tdee_stats.get("energy_balance", 0),
            "reason": f"TDEE: {tdee}, Status: {tdee_stats.get('status')}, Objetivo: {profile.goal_type}"
        }

