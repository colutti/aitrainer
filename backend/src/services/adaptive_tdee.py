from datetime import date, timedelta, datetime
from typing import List

from src.api.models.weight_log import WeightLog
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

    def _filter_outliers(self, logs: List[WeightLog]) -> tuple[List[WeightLog], int]:
        """
        Filters out transient weight anomalies and handles 'step changes'.
        Logic:
        1. Calculate daily delta from last valid log.
        2. If delta > 1.0 kg (Abs), flag as potential outlier.
        3. Look ahead: does it stay there?
           - If YES (e.g. 78 -> 76.5 -> 76.5): It's a Step Change. 
             Discard history BEFORE the step (reset baseline).
           - If NO (e.g. 76.5 -> 78 -> 76.5): It's a Transient Spike.
             Discard the anomaly.
        
        Returns:
            tuple: (List[WeightLog], int: number of ignored/discarded logs)
        """
        if len(logs) < 3:
            return logs, 0

        # Sort just in case
        sorted_logs = sorted(logs, key=lambda x: x.date)
        
        # Start with the first log
        clean_logs = [sorted_logs[0]]
        last_valid_log = sorted_logs[0]
        ignored_count = 0
        
        i = 1
        while i < len(sorted_logs):
            curr = sorted_logs[i]
            
            delta = abs(curr.weight_kg - last_valid_log.weight_kg)
            days_diff = (curr.date - last_valid_log.date).days
            
            # If days_diff is large, a big jump is natural, not outlier.
            # Only flag if jump happened in short time (e.g. < 3 days)
            if delta > self.MAX_DAILY_WEIGHT_CHANGE and days_diff <= 3:
                # Potential Anomaly. Check next log (future) if exists
                if i + 1 < len(sorted_logs):
                    next_log = sorted_logs[i+1]
                    
                    # Compare next log against the last valid log (baseline)
                    dist_to_baseline = abs(next_log.weight_kg - last_valid_log.weight_kg)
                    
                    # Case A: Spike (76 -> 78 -> 76). Next log is closer to baseline than current outlier.
                    if dist_to_baseline < delta:
                        # It returned close to baseline. Skip 'curr'
                        logger.warning("Ignoring transient weight spike: %s kg on %s", curr.weight_kg, curr.date)
                        ignored_count += 1
                        i += 1
                        continue
                        
                    # Case B: Step Change (78 -> 76.5 -> 76.5). Next log confirms new level.
                    # Or Case C: Just weird chaos.
                    # If it didn't return to baseline, we assume Step Change.
                    # RESET baseline to 'curr'.
                    logger.warning("Detected Step Change in weight: %s -> %s. Resetting baseline.", last_valid_log.weight_kg, curr.weight_kg)
                    # Count everything we had so far as "ignored" for the current trend
                    ignored_count += len(clean_logs)
                    clean_logs = [curr] # Restart list with current as new start
                    last_valid_log = curr
                    i += 1
                    continue
                else:
                    # Last log is big jump. Cannot verify.
                    # Let's keep it but log.
                    logger.warning("Last weight log shows large jump: %s -> %s", last_valid_log.weight_kg, curr.weight_kg)
                    clean_logs.append(curr)
                    last_valid_log = curr
                    i += 1
            else:
                clean_logs.append(curr)
                last_valid_log = curr
                i += 1
                
        return clean_logs, ignored_count

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
                "end_weight": float,
                "outliers_count": int,
                "weight_logs_count": int
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
        # Filter outliers / step changes first
        weight_logs, outliers_count = self._filter_outliers(weight_logs)
        
        # Sort logs by date ascending (should be already sorted by filter, but safely ensure)
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
            log_item for log_item in nutrition_logs 
            if period_start <= log_item.date.date() <= period_end
        ]
        
        if not relevant_nutrition:
             return self._insufficient_data_response()
 
        total_calories = sum(log_item.calories for log_item in relevant_nutrition)
        avg_calories_logged = total_calories / len(relevant_nutrition)
        
        # 4. Calculate TDEE
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
        
        conf_data = self._calculate_confidence(
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
            "confidence": conf_data["level"],
            "confidence_reason": conf_data["reason"],
            "avg_calories": int(round(avg_calories_logged)),
            "weight_change_per_week": round(weekly_change, 2),
            "energy_balance": round(energy_balance, 1),
            "status": status,
            "is_stable": is_stable,
            "logs_count": len(relevant_nutrition), # Backwards compatibility
            "nutrition_logs_count": len(relevant_nutrition),
            "startDate": period_start.isoformat(),
            "endDate": period_end.isoformat(),
            "start_weight": round(start_weight, 2),
            "end_weight": round(end_weight, 2),
            "latest_weight": weight_logs[-1].weight_kg,
            "daily_target": daily_target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type,
            "outliers_count": outliers_count,
            "weight_logs_count": len(weight_logs)
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
        
        valid_logs = [log_item for log_item in logs if log_item.body_fat_pct is not None]
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
            "end_fat_pct": round(last.body_fat_pct, 1),
            "start_muscle_pct": round(first.muscle_mass_pct, 1) if first.muscle_mass_pct else None,
            "end_muscle_pct": round(last.muscle_mass_pct, 1) if last.muscle_mass_pct else None
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
            # Guard against zero variance which causes RuntimeWarning
            if np.std(y_arr) == 0 or np.std(x_arr) == 0:
                r_value = 0.0  # No correlation when data is constant
            else:
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




    def _calculate_confidence(self, days_elapsed: int, weight_count: int, nutrition_count: int, expected_logs: int) -> dict:
        """
        Determines confidence level and reason.
        """
        nutrition_adherence = nutrition_count / expected_logs if expected_logs > 0 else 0
        
        if days_elapsed < 14:
            return {"level": "low", "reason": f"Histórico muito curto ({days_elapsed} dias). Mínimo recomendado: 14 dias."}
            
        if nutrition_adherence > 0.85:
            return {"level": "high", "reason": "Excelente consistência de dados!"}
        elif nutrition_adherence > 0.6:
            return {"level": "medium", "reason": "Aderência parcial aos registros (>60%). Tente registrar todos os dias."}
        else:
            return {"level": "low", "reason": "Muitos dias sem registro de refeições (<60%). A precisão do cálculo depende do rastreamento diário."}

    def _insufficient_data_response(self) -> dict:
        return {
            "tdee": 0,
            "confidence": "none",
            "reason": "Dados insuficientes para cálculo. Continue registrando peso e dieta por pelo menos 1 semana."
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
            "reason": f"TDEE: {tdee} (Based on Weekly Average including workouts), Status: {tdee_stats.get('status')}, Goal: {profile.goal_type}"
        }

