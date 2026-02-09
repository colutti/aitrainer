from datetime import date, timedelta, datetime
from typing import List

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
    MAX_DAILY_WEIGHT_CHANGE = 1.0  # kg (flag as anomaly if higher)
    EMA_SPAN = 10  # Days span for EMA (MacroFactor style: 7-14)

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
                    next_log = sorted_logs[i + 1]

                    # Compare next log against the last valid log (baseline)
                    dist_to_baseline = abs(
                        next_log.weight_kg - last_valid_log.weight_kg
                    )

                    # Case A: Spike (76 -> 78 -> 76). Next log is closer to baseline than current outlier.
                    if dist_to_baseline < delta:
                        # It returned close to baseline. Skip 'curr'
                        logger.info(
                            "Ignoring transient weight spike: %s kg on %s",
                            curr.weight_kg,
                            curr.date,
                        )
                        ignored_count += 1
                        i += 1
                        continue

                    # Case B: Step Change (78 -> 76.5 -> 76.5). Next log confirms new level.
                    # Or Case C: Just weird chaos.
                    # If it didn't return to baseline, we assume Step Change.
                    # RESET baseline to 'curr'.
                    logger.info(
                        "Detected Step Change in weight: %s -> %s. Resetting baseline.",
                        last_valid_log.weight_kg,
                        curr.weight_kg,
                    )
                    # Count everything we had so far as "ignored" for the current trend
                    ignored_count += len(clean_logs)
                    clean_logs = [curr]  # Restart list with current as new start
                    last_valid_log = curr
                    i += 1
                    continue
                else:
                    # Last log is big jump. Cannot verify.
                    # Let's keep it but log.
                    logger.info(
                        "Last weight log shows large jump: %s -> %s",
                        last_valid_log.weight_kg,
                        curr.weight_kg,
                    )
                    clean_logs.append(curr)
                    last_valid_log = curr
                    i += 1
            else:
                clean_logs.append(curr)
                last_valid_log = curr
                i += 1

        return clean_logs, ignored_count

    def calculate_ema_trend(self, weight_kg: float, prev_trend: float | None) -> float:
        """
        Calculates the new Trend Weight using Exponential Moving Average.
        Formula: Trend = Actual * alpha + Prev_Trend * (1 - alpha)
        Alpha = 2 / (span + 1)
        """
        if prev_trend is None:
            return weight_kg

        alpha = 2 / (self.EMA_SPAN + 1)
        return (weight_kg * alpha) + (prev_trend * (1 - alpha))

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
        weight_logs = self.db.get_weight_logs_by_date_range(
            user_email, start_date, end_date
        )
        nutrition_logs = self.db.get_nutrition_logs_by_date_range(
            user_email,
            datetime(start_date.year, start_date.month, start_date.day),
            datetime(end_date.year, end_date.month, end_date.day),
        )

        if len(weight_logs) < 2 or len(nutrition_logs) < self.MIN_DATA_DAYS:
            logger.info(
                "Insufficient data for TDEE calculation for user %s. Using fallback.", user_email
            )
            return self._calculate_fallback_tdee(user_email, weight_logs, nutrition_logs)

        # Capture actual latest weight BEFORE any filtering (Bug Fix #1)
        weight_logs.sort(key=lambda x: x.date)
        actual_latest_weight = weight_logs[-1].weight_kg

        # Preserve raw logs for body composition calculation (Bug Fix #3)
        weight_logs_raw = list(weight_logs)

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
            logger.info("Data range too short after filtering for user %s. Using fallback.", user_email)
            return self._calculate_fallback_tdee(user_email, weight_logs_raw, nutrition_logs)

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
            log_item
            for log_item in nutrition_logs
            if period_start <= log_item.date.date() <= period_end
        ]

        if not relevant_nutrition:
            logger.info("No nutrition logs in the weight period for user %s. Using fallback.", user_email)
            return self._calculate_fallback_tdee(user_email, weight_logs, nutrition_logs)

        total_calories = sum(log_item.calories for log_item in relevant_nutrition)
        
        # Adherence Neutrality Logic:
        # Instead of just averaging logged days, we check for 'holes'.
        # If user logs 10/14 days, we assume the other 4 days were 'average' (avg_calories_logged).
        # This is already what sum/count does.
        # However, we want to flag 'Low Confidence' if gaps are too large (> 3 days).
        
        adherence_rate = len(relevant_nutrition) / (days_elapsed + 1)
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
            days_elapsed,  # Expected logs
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

            adjustment: float = 0
            if goal_type == "lose":
                adjustment = -1 * abs(goal_rate) * 1100
            elif goal_type == "gain":
                adjustment = abs(goal_rate) * 1100

            daily_target = int(round(tdee + adjustment))
            daily_target = max(1000, daily_target)

        # 7. Body Composition Analysis (use FILTERED logs to avoid being distorted by outliers - Refined Bug Fix #3)
        comp_changes = self._calculate_body_composition_changes(weight_logs)

        # 8. Projection & ETA
        weeks_to_goal = None
        goal_eta_weeks = None
        if profile and profile.target_weight and goal_type != "maintain":
            weight_diff = abs(weight_logs[-1].weight_kg - profile.target_weight)

            # Goal ETA (Theoretical)
            if goal_rate > 0:
                goal_eta_weeks = round(weight_diff / goal_rate, 1)

            # Real ETA (Trend based)
            # Use weekly_change if it favors the goal
            favors_goal = False
            if goal_type == "lose" and weekly_change < -0.05:  # At least some loss
                favors_goal = True
            elif goal_type == "gain" and weekly_change > 0.05:  # At least some gain
                favors_goal = True

            if favors_goal:
                weeks_to_goal = round(weight_diff / abs(weekly_change), 1)

        avg_protein = sum(
            log.protein_grams for log in relevant_nutrition if log.protein_grams
        ) / len(relevant_nutrition)
        avg_carbs = sum(log.carbs_grams for log in relevant_nutrition if log.carbs_grams) / len(
            relevant_nutrition
        )
        avg_fat = sum(log.fat_grams for log in relevant_nutrition if log.fat_grams) / len(
            relevant_nutrition
        )

        # 9. Macro Targets & Stability
        macro_targets = None
        stability_score = None
        if daily_target:
             macro_targets = self._calculate_macro_targets(daily_target, actual_latest_weight)
             stability_score = self._calculate_stability_score(daily_target, relevant_nutrition)

        result = {
            "tdee": int(round(tdee)),
            "confidence": conf_data["level"],
            "confidence_reason": conf_data["reason"],
            "avg_calories": int(round(avg_calories_logged)),
            "avg_protein": int(round(avg_protein)),
            "avg_carbs": int(round(avg_carbs)),
            "avg_fat": int(round(avg_fat)),
            "weight_change_per_week": round(weekly_change, 2),
            "energy_balance": round(energy_balance, 1),
            "status": status,
            "is_stable": is_stable,
            "logs_count": len(relevant_nutrition),  # Backwards compatibility
            "nutrition_logs_count": len(relevant_nutrition),
            "startDate": period_start.isoformat(),
            "endDate": period_end.isoformat(),
            "start_weight": round(start_weight, 2),
            "end_weight": round(end_weight, 2),
            "latest_weight": actual_latest_weight,  # Bug Fix #1: use pre-filter value
            "daily_target": daily_target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type,
            "target_weight": profile.target_weight if profile else None,
            "weeks_to_goal": weeks_to_goal,
            "goal_eta_weeks": goal_eta_weeks,
            "outliers_count": outliers_count,
            "weight_logs_count": len(weight_logs),
            "weight_trend": [
                {
                    "date": log.date.isoformat() if isinstance(log.date, date) else log.date,
                    "weight": log.weight_kg,
                    "trend": round(log.trend_weight, 2) if log.trend_weight else None,
                }
                for log in weight_logs
            ],
            "expenditure_trend": "stable", # Default to stable, could be refined with historical TDEE
            "consistency_score": int(round(adherence_rate * 100)),
            "macro_targets": macro_targets,
            "stability_score": stability_score,
            "consistency": [
                {
                    "date": (date.today() - timedelta(days=i)).isoformat(),
                    "weight": (date.today() - timedelta(days=i))
                    in {log.date for log in weight_logs_raw},
                    "nutrition": (date.today() - timedelta(days=i))
                    in {log.date.date() for log in nutrition_logs},
                }
                for i in range(27, -1, -1)
            ],
            "calorie_trend": [
                {
                    "date": (period_start + timedelta(days=i)).isoformat(),
                    "calories": next(
                        (
                            log.calories
                            for log in relevant_nutrition
                            if log.date.date() == (period_start + timedelta(days=i))
                        ),
                        0,
                    ),
                }
                for i in range((period_end - period_start).days + 1)
            ],
        }

        if comp_changes:
            result.update(comp_changes)

        # Include BMR from scale if available in latest log
        latest_log = weight_logs[-1]
        if latest_log.bmr:
            result["scale_bmr"] = latest_log.bmr

        return result

    def _calculate_body_composition_changes(self, logs: List[WeightLog]) -> dict | None:
        """Calculate fat and muscle mass changes using actual scale data."""
        # Filter to logs with body composition data
        valid_logs = [
            log_item for log_item in logs if log_item.body_fat_pct is not None
        ]
        if len(valid_logs) < 2:
            return None

        first = valid_logs[0]
        last = valid_logs[-1]

        # Fat calculation using REAL weights from logs (not regression)
        # Use casts to satisfy Mypy as we already filtered None in valid_logs
        from typing import cast
        fat_mass_start = first.weight_kg * (cast(float, first.body_fat_pct) / 100.0)
        fat_mass_end = last.weight_kg * (cast(float, last.body_fat_pct) / 100.0)
        fat_change = fat_mass_end - fat_mass_start

        # Muscle calculation: use REAL muscle_mass_pct if available (Bug Fix #2)
        muscle_change = None
        if first.muscle_mass_pct and last.muscle_mass_pct:
            muscle_mass_start = first.weight_kg * (first.muscle_mass_pct / 100.0)
            muscle_mass_end = last.weight_kg * (last.muscle_mass_pct / 100.0)
            muscle_change = muscle_mass_end - muscle_mass_start
        else:
            # Fallback to derived calculation only if muscle data unavailable
            total_weight_change = last.weight_kg - first.weight_kg
            muscle_change = total_weight_change - fat_change

        return {
            "fat_change_kg": round(fat_change, 2),
            "muscle_change_kg": round(muscle_change, 2),
            "start_fat_pct": round(cast(float, first.body_fat_pct), 1),
            "end_fat_pct": round(cast(float, last.body_fat_pct), 1),
            "start_muscle_pct": round(cast(float, first.muscle_mass_pct), 1)
            if first.muscle_mass_pct
            else None,
            "end_muscle_pct": round(cast(float, last.muscle_mass_pct), 1)
            if last.muscle_mass_pct
            else None,
        }

    def _calculate_regression_trend(
        self, logs: List[WeightLog]
    ) -> tuple[float, float, float]:
        """
        Calculates the linear regression trend of weight logs.
        Returns (slope, intercept, r_value).
        Slope is kg per day.
        """
        import numpy as np

        if not logs:
            return 0.0, 0.0, 0.0

        start_date = logs[0].date
        x = []  # Days since start
        y = []  # Weights

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

            # --- Weighted Regression (MacroFactor Style) ---
            # Recent points have more 'influence' on the slope.
            # We use an exponential weight: w = e^(days_from_end * k)
            # where k < 0. For today, w=1.0. For 14 days ago, w is smaller.
            
            # Halving time for weight: 
            # -0.07 ≈ 10 days
            # -0.10 ≈ 7 days (High Responsiveness)
            k = -0.10
            max_days = x[-1]
            weights = np.exp([k * (max_days - d) for d in x])
            
            m, c = np.polyfit(x_arr, y_arr, 1, w=weights)

            # Simple R approximation (not strictly needed but useful for confidence later)
            # Guard against zero variance which causes RuntimeWarning
            if np.std(y_arr) == 0 or np.std(x_arr) == 0:
                r_value = 0.0  # No correlation when data is constant
            else:
                correlation_matrix = np.corrcoef(x_arr, y_arr)
                r_value = (
                    correlation_matrix[0, 1]
                    if correlation_matrix.shape == (2, 2)
                    else 0.0
                )

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

    def _calculate_confidence(
        self,
        days_elapsed: int,
        weight_count: int,
        nutrition_count: int,
        expected_logs: int,
    ) -> dict:
        """
        Determines confidence level and reason.
        """
        nutrition_adherence = (
            nutrition_count / expected_logs if expected_logs > 0 else 0
        )

        if days_elapsed < 14:
            return {
                "level": "low",
                "reason": f"Histórico muito curto ({days_elapsed} dias). Mínimo recomendado: 14 dias.",
            }

        if nutrition_adherence > 0.85:
            return {"level": "high", "reason": "Excelente consistência de dados!"}
        elif nutrition_adherence > 0.6:
            return {
                "level": "medium",
                "reason": f"Aderência parcial ({nutrition_adherence*100:.0f}%). Recomenda-se registrar todos os dias para maior precisão.",
            }
        else:
            return {
                "level": "low",
                "reason": f"Muitos gaps nos registros ({nutrition_adherence*100:.0f}%). A estimativa pode estar distorcida por dias não registrados.",
            }

    def _insufficient_data_response(self) -> dict:
        return {
            "tdee": 0,
            "confidence": "none",
            "reason": "Dados insuficientes para cálculo. Continue registrando peso e dieta por pelo menos 1 semana.",
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
                "reason": "Insufficient data for TDEE",
            }

        # 2. Get User Profile for Goal
        profile = self.db.get_user_profile(user_email)
        if not profile:
            return {
                "tdee": int(tdee),
                "daily_target": int(tdee),  # Maintenance default
                "reason": "No profile found",
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

        adjustment: float = 0
        if profile.goal_type == "lose":
            adjustment = -1 * abs(goal_rate) * 1100
        elif profile.goal_type == "gain":  # or gain_weight
            adjustment = abs(goal_rate) * 1100

        daily_target = tdee + adjustment

        # Sanity caps
        daily_target = max(1000, daily_target)  # Never recommend below 1000

        return {
            "tdee": int(tdee),
            "daily_target": int(daily_target),
            "status": tdee_stats.get("status", "maintenance"),
            "energy_balance": tdee_stats.get("energy_balance", 0),
            "reason": f"TDEE: {tdee} (Based on Weekly Average including workouts), Status: {tdee_stats.get('status')}, Goal: {profile.goal_type}",
        }
    def _calculate_macro_targets(self, daily_target: int, weight_kg: float) -> dict:
        """Calculates macro targets based on body weight and calorie goal."""
        # 2.0g Protein per kg (standard for active individuals)
        protein_g = int(round(weight_kg * 2.0))
        # 25% Fat (standard healthy range)
        fat_g = int(round((daily_target * 0.25) / 9))
        # Carbs = remainder
        carb_cals = daily_target - (protein_g * 4) - (fat_g * 9)
        # Ensure we don't return negative carbs (if protein/fat already exceed target)
        carb_g = int(round(max(0, carb_cals / 4)))

        return {"protein": protein_g, "carbs": carb_g, "fat": fat_g}

    def _calculate_stability_score(
        self, target: int, nutrition_logs: list[NutritionLog]
    ) -> int:
        """Calculates calorie consistency score (0-100) based on last 7 logs."""
        if not nutrition_logs or target <= 0:
            return 0

        last_7_logs = sorted(nutrition_logs, key=lambda x: x.date, reverse=True)[:7]
        if not last_7_logs:
            return 0

        # Stability = % of days within ±10% of target
        window = target * 0.10
        stable_days = sum(
            1 for log in last_7_logs if abs(log.calories - target) <= window
        )

        return int(round((stable_days / len(last_7_logs)) * 100))

    def _calculate_fallback_tdee(self, user_email: str, weight_logs: List[WeightLog], nutrition_logs: List[NutritionLog]) -> dict:
        """
        Provides a safe TDEE estimate when adaptive data is missing or unstable.
        """
        profile = self.db.get_user_profile(user_email)
        
        # Latest weight (raw)
        latest_weight = 70.0 # Extreme fallback
        if weight_logs:
            sorted_raw = sorted(weight_logs, key=lambda x: x.date)
            latest_weight = sorted_raw[-1].weight_kg
        
        # 1. BMR from Scale (Preferred)
        scale_bmr = next((log.bmr for log in reversed(weight_logs) if log.bmr), None)
        
        # 2. BMR from Profile (Fallback)
        calculated_bmr = 0.0
        if profile and profile.height and profile.age:
            try:
                age = profile.age
                if profile.gender == 'Feminino' or profile.gender == 'female':
                    calculated_bmr = (10 * latest_weight) + (6.25 * profile.height) - (5 * age) - 161
                else:
                    calculated_bmr = (10 * latest_weight) + (6.25 * profile.height) - (5 * age) + 5
            except Exception:
                pass
        
        base_bmr = scale_bmr or calculated_bmr or (latest_weight * 22) or 1500
        
        # 3. Activity Factor (Default to 1.35)
        tdee_estimate = base_bmr * 1.35
        
        # 4. Consistency & Target
        days_covered = 7 # Default window for consistency
        if weight_logs and len(weight_logs) >= 2:
             days_covered = (weight_logs[-1].date - weight_logs[0].date).days
        
        adherence_rate = len(nutrition_logs) / (days_covered + 1) if days_covered > 0 else 0
        
        daily_target = int(round(tdee_estimate))
        goal_type = "maintain"
        goal_rate = 0.0
        if profile:
            goal_type = profile.goal_type
            goal_rate = profile.weekly_rate or 0.0
            adjustment = 0
            if goal_type == "lose":
                adjustment = -1 * abs(goal_rate) * 1100
            elif goal_type == "gain":
                adjustment = abs(goal_rate) * 1100
            daily_target = int(round(tdee_estimate + adjustment))
            daily_target = max(1000, daily_target)

        return {
            "tdee": int(round(tdee_estimate)),
            "confidence": "none",
            "confidence_reason": "Utilizando estimativa baseada em seu metabolismo basal (BMR) devido a histórico de dados insuficiente ou instável.",
            "avg_calories": int(round(sum(n.calories for n in nutrition_logs)/len(nutrition_logs))) if nutrition_logs else 0,
            "weight_change_per_week": 0.0,
            "energy_balance": 0.0,
            "status": "maintenance",
            "is_stable": True,
            "logs_count": len(nutrition_logs),
            "nutrition_logs_count": len(nutrition_logs),
            "startDate": weight_logs[0].date.isoformat() if weight_logs else date.today().isoformat(),
            "endDate": weight_logs[-1].date.isoformat() if weight_logs else date.today().isoformat(),
            "latest_weight": latest_weight,
            "daily_target": daily_target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type,
            "consistency_score": int(round(adherence_rate * 100)),
            "macro_targets": self._calculate_macro_targets(daily_target, latest_weight),
            "weight_trend": [],
            "consistency": [],
            "calorie_trend": []
        }
