"""
Service for calculating Adaptive TDEE based on weight and nutrition history.
"""

from datetime import date, timedelta, datetime
from typing import List, TYPE_CHECKING, cast

import numpy as np

from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.core.logs import logger

if TYPE_CHECKING:
    from src.services.database import MongoDatabase
    from src.api.models.user_profile import UserProfile


class AdaptiveTDEEService:
    """
    Service for calculating Adaptive TDEE based on weight and nutrition history.

    Algorithm:
    TDEE = Average_Calories_Consumed - (Weight_Change_kg * 7700 / Days_Elapsed)

    Using Exponential Moving Average (EMA) for weight smoothing.
    """

    # Constants — Energy Content (Forbes/Hall model)
    KCAL_PER_KG_FAT_MASS = 9400
    KCAL_PER_KG_LEAN_MASS = 1800
    KCAL_PER_KG_DEFAULT = 7700  # Fallback when no body fat data

    MIN_DATA_DAYS = 3

    # Regression config
    MIN_DATA_DAYS_FOR_REGRESSION = 10

    # Sanity Limits
    MIN_TDEE = 1200
    MAX_TDEE = 5000
    MAX_DAILY_WEIGHT_CHANGE = 1.0  # kg (flag as anomaly if higher)
    EMA_SPAN = 21  # Days span for EMA (21-day window)
    TDEE_OBS_EMA_SPAN = 21  # EMA span for daily TDEE observations
    MAX_INTERPOLATION_GAP = 14  # Maximum days to interpolate linearly

    # Coaching check-in
    MAX_WEEKLY_ADJUSTMENT = 100  # was 75, now actually used
    CHECK_IN_INTERVAL_DAYS = 7

    # Lookback
    DEFAULT_LOOKBACK_WEEKS = 4  # was 3

    # Safety floors (gender-specific, NIH/Harvard)
    MIN_CALORIES_FEMALE = 1200
    MIN_CALORIES_MALE = 1500
    MAX_DEFICIT_PCT = 0.30  # Never exceed 30% deficit

    # Outlier detection
    OUTLIER_MODIFIED_Z_THRESHOLD = 3.5

    def __init__(self, db: "MongoDatabase"):
        """Initialize the AdaptiveTDEEService with a database connection."""
        self.db = db

    def _filter_outliers(self, logs: List[WeightLog]) -> tuple[List[WeightLog], int]:
        """
        Filters out weight anomalies using a two-pass approach:
        1. Modified Z-Score (statistical) — catches extreme one-off values
        2. Contextual (semantic) — handles step changes and transient spikes

        Returns:
            tuple: (filtered_logs, count_of_removed_logs)
        """
        if len(logs) < 3:
            return logs, 0

        sorted_logs = sorted(logs, key=lambda x: x.date)

        # === Pass 1: Modified Z-Score ===
        weights = np.array([log.weight_kg for log in sorted_logs])
        median = np.median(weights)
        mad = np.median(np.abs(weights - median))

        statistical_clean = []
        stat_removed = 0

        if mad > 0:
            modified_z_scores = 0.6745 * (weights - median) / mad
            for i, log in enumerate(sorted_logs):
                if abs(modified_z_scores[i]) > self.OUTLIER_MODIFIED_Z_THRESHOLD:
                    logger.info(
                        "Modified Z-Score outlier: %.1f kg on %s (z=%.2f)",
                        log.weight_kg, log.date, modified_z_scores[i],
                    )
                    stat_removed += 1
                else:
                    statistical_clean.append(log)
        else:
            # MAD=0 means all values are the same (or very close), no outliers
            statistical_clean = list(sorted_logs)

        if len(statistical_clean) < 3:
            return statistical_clean, stat_removed

        # === Pass 2: Contextual (spike/step-change) ===
        clean_logs = [statistical_clean[0]]
        last_valid_log = statistical_clean[0]
        contextual_removed = 0

        i = 1
        while i < len(statistical_clean):
            curr = statistical_clean[i]
            delta = abs(curr.weight_kg - last_valid_log.weight_kg)
            days_diff = (curr.date - last_valid_log.date).days

            if delta > self.MAX_DAILY_WEIGHT_CHANGE and days_diff <= 3:
                if i + 1 < len(statistical_clean):
                    next_log = statistical_clean[i + 1]
                    dist_to_baseline = abs(next_log.weight_kg - last_valid_log.weight_kg)

                    # Case A: Spike
                    if dist_to_baseline < delta:
                        logger.info(
                            "Ignoring transient weight spike: %s kg on %s",
                            curr.weight_kg, curr.date,
                        )
                        contextual_removed += 1
                        i += 1
                        continue

                    # Case B: Step Change
                    logger.info(
                        "Detected Step Change: %s -> %s. Resetting baseline.",
                        last_valid_log.weight_kg, curr.weight_kg,
                    )
                    contextual_removed += len(clean_logs)
                    clean_logs = [curr]
                    last_valid_log = curr
                    i += 1
                    continue

                logger.info(
                    "Last weight log shows large jump: %s -> %s",
                    last_valid_log.weight_kg, curr.weight_kg,
                )

            clean_logs.append(curr)
            last_valid_log = curr
            i += 1

        return clean_logs, stat_removed + contextual_removed

    def _estimate_energy_per_kg(self, body_fat_pct: float | None, slope: float) -> float:
        """
        Estimates energy content per kg of weight change using Forbes/Hall model.

        Higher body fat → more fat lost per kg → higher kcal/kg.
        Rapid loss → more lean tissue lost → lower kcal/kg.

        Args:
            body_fat_pct: User's body fat percentage (None = use default 7700).
            slope: Daily weight change in kg/day (negative = losing).

        Returns:
            Estimated kcal per kg of weight change (range: ~5600-8640).
        """
        if body_fat_pct is None:
            return self.KCAL_PER_KG_DEFAULT

        # Base fat fraction from body fat % (Forbes model)
        # At 25% bf: fat_fraction = 0.75 (baseline)
        # Each 1% bf above/below 25% shifts fraction by 0.005
        fat_fraction = 0.75 + (body_fat_pct - 25) * 0.005

        # Rapid loss penalty: losing > 0.5 kg/week means more lean tissue lost
        rate_weekly = abs(slope * 7)
        if rate_weekly > 0.5:
            fat_fraction -= 0.05 * (rate_weekly - 0.5)

        # Clamp to physiological bounds
        fat_fraction = max(0.50, min(0.90, fat_fraction))

        return fat_fraction * self.KCAL_PER_KG_FAT_MASS + (1 - fat_fraction) * self.KCAL_PER_KG_LEAN_MASS

    def calculate_ema_trend(self, weight_kg: float, prev_trend: float | None) -> float:
        """
        Calculates the new Trend Weight using Exponential Moving Average.
        """
        if prev_trend is None:
            return weight_kg

        alpha = 2 / (self.EMA_SPAN + 1)
        return (weight_kg * alpha) + (prev_trend * (1 - alpha))

    def _interpolate_weight_gaps(
        self, weight_logs: list[WeightLog], max_gap_days: int | None = None
    ) -> dict[date, float]:
        """
        Interpola linealmente pesos entre pesagens (até max_gap_days de intervalo).

        Exemplo:
        - logs = [day1=80kg, day15=73.6kg]  (gap de 14 dias)
        - Retorna: {day1: 80.0, day2: 79.54, day3: 79.09, ..., day15: 73.6}

        Se gap > max_gap_days, usa o último valor conhecido para preencher o gap.

        Args:
            weight_logs: Lista de WeightLog ordenados por data
            max_gap_days: Máximo intervalo em dias para interpolar (padrão: MAX_INTERPOLATION_GAP)

        Returns:
            Dict ordenado {date: weight_kg} com todas as datas no range
        """
        if max_gap_days is None:
            max_gap_days = self.MAX_INTERPOLATION_GAP

        if not weight_logs:
            return {}

        sorted_logs = sorted(weight_logs, key=lambda x: x.date)
        result = {}

        for i, log in enumerate(sorted_logs):
            # Adiciona o peso registrado
            result[log.date] = log.weight_kg

            # Se não é o último log, processa o gap até o próximo
            if i < len(sorted_logs) - 1:
                next_log = sorted_logs[i + 1]
                gap_days = (next_log.date - log.date).days

                if gap_days <= 1:
                    # Sem gap, próxima iteração vai adicionar próximo log
                    continue

                # Calcula interpolação linear
                weight_diff = next_log.weight_kg - log.weight_kg
                daily_change = weight_diff / gap_days

                if gap_days <= max_gap_days:
                    # Interpola linear entre os pesos
                    for day_offset in range(1, gap_days):
                        interpolated_date = log.date + timedelta(days=day_offset)
                        interpolated_weight = log.weight_kg + (daily_change * day_offset)
                        result[interpolated_date] = interpolated_weight
                else:
                    # Gap muito grande, usa o último valor conhecido
                    for day_offset in range(1, gap_days):
                        interpolated_date = log.date + timedelta(days=day_offset)
                        result[interpolated_date] = log.weight_kg

        return dict(sorted(result.items()))

    def _compute_daily_trend(self, daily_weight_series: dict[date, float]) -> dict[date, float]:
        """
        Calcula EMA (21 dias) sobre a série diária de pesos.

        EMA: trend_today = alpha * weight_today + (1-alpha) * trend_yesterday
        alpha = 2 / (span + 1) = 2 / 22 ≈ 0.0909

        Args:
            daily_weight_series: Dict ordenado {date: weight_kg}

        Returns:
            Dict {date: trend_kg} com valores suavizados
        """
        if not daily_weight_series:
            return {}

        sorted_dates = sorted(daily_weight_series.keys())
        result = {}
        alpha = 2 / (self.EMA_SPAN + 1)

        for i, current_date in enumerate(sorted_dates):
            current_weight = daily_weight_series[current_date]

            if i == 0:
                # Primeira data: trend = weight
                result[current_date] = current_weight
            else:
                # EMA: trend = alpha * weight + (1-alpha) * prev_trend
                prev_trend = result[sorted_dates[i - 1]]
                result[current_date] = (current_weight * alpha) + (prev_trend * (1 - alpha))

        return result

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    def calculate_tdee(self, user_email: str, lookback_weeks: int = 4) -> dict:
        """
        Calculates the user's TDEE over the specified lookback period.
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
                "Insufficient data for TDEE for user %s. Using fallback.", user_email
            )
            return self._calculate_fallback_tdee(
                user_email, weight_logs, nutrition_logs
            )

        # Capture actual latest weight BEFORE any filtering (Bug Fix #1)
        weight_logs.sort(key=lambda x: x.date)
        actual_latest_weight = weight_logs[-1].weight_kg
        weight_logs_raw = list(weight_logs)

        # 2. Process Weight Data (Trend Estimation)
        weight_logs, outliers_count = self._filter_outliers(weight_logs)
        weight_logs.sort(key=lambda x: x.date)

        # Calculate trend using Linear Regression
        slope, intercept, _ = self._calculate_regression_trend(weight_logs)
        days_elapsed = (weight_logs[-1].date - weight_logs[0].date).days

        if days_elapsed < self.MIN_DATA_DAYS:
            logger.info("Data range too short for user %s. Using fallback.", user_email)
            return self._calculate_fallback_tdee(
                user_email, weight_logs_raw, nutrition_logs
            )

        # Theoretical weight change based on the trend
        start_weight = intercept
        end_weight = intercept + (slope * days_elapsed)
        total_weight_change = end_weight - start_weight

        # 3. Process Nutrition Data
        period_start = weight_logs[0].date
        period_end = weight_logs[-1].date

        relevant_nutrition = []
        for log_item in nutrition_logs:
            # Handle both datetime and date objects
            log_date_only = (
                log_item.date.date()
                if isinstance(log_item.date, datetime)
                else log_item.date
            )
            if period_start <= log_date_only <= period_end:
                relevant_nutrition.append(log_item)

        if not relevant_nutrition:
            logger.info("No nutrition logs for user %s. Using fallback.", user_email)
            return self._calculate_fallback_tdee(
                user_email, weight_logs, nutrition_logs
            )

        total_calories = sum(log_item.calories for log_item in relevant_nutrition)
        adherence_rate = len(relevant_nutrition) / (days_elapsed + 1)
        avg_calories_logged = total_calories / len(relevant_nutrition)

        # 4. Calculate TDEE (dynamic energy density)
        latest_body_fat = next(
            (log.body_fat_pct for log in reversed(weight_logs) if log.body_fat_pct is not None),
            None,
        )
        energy_per_kg = self._estimate_energy_per_kg(latest_body_fat, slope)
        daily_surplus_deficit = slope * energy_per_kg
        tdee = avg_calories_logged - daily_surplus_deficit

        # 5. Sanity Checks & Confidence
        tdee = max(self.MIN_TDEE, min(self.MAX_TDEE, tdee))
        energy_balance = avg_calories_logged - tdee
        status = "maintenance"
        if energy_balance < -150:
            status = "deficit"
        elif energy_balance > 150:
            status = "surplus"
        is_stable = abs(energy_balance) < 150

        conf_data = self._calculate_confidence(
            days_elapsed, len(relevant_nutrition), days_elapsed
        )
        weekly_change = (total_weight_change / days_elapsed) * 7

        # 6. Include Goal & Target Info
        goal_rate, goal_type = 0.0, "maintain"
        profile = self.db.get_user_profile(user_email)

        # Use coaching check-in for daily_target
        daily_target = self._calculate_coaching_target(
            tdee, avg_calories_logged, weekly_change, profile
        )

        if profile:
            goal_rate, goal_type = profile.weekly_rate or 0.0, profile.goal_type

        # 7. Body Composition Analysis
        comp_changes = self._calculate_body_composition_changes(weight_logs)

        # 8. Projection & ETA
        weeks_to_goal, goal_eta_weeks = None, None
        if profile and profile.target_weight and goal_type != "maintain":
            weight_diff = abs(weight_logs[-1].weight_kg - profile.target_weight)
            if goal_rate > 0:
                goal_eta_weeks = round(weight_diff / goal_rate, 1)
            favors_goal = (goal_type == "lose" and weekly_change < -0.05) or (
                goal_type == "gain" and weekly_change > 0.05
            )
            if favors_goal:
                weeks_to_goal = round(weight_diff / abs(weekly_change), 1)

        avg_protein = sum(
            log.protein_grams for log in relevant_nutrition if log.protein_grams
        ) / len(relevant_nutrition)
        avg_carbs = sum(
            log.carbs_grams for log in relevant_nutrition if log.carbs_grams
        ) / len(relevant_nutrition)
        avg_fat = sum(log.fat_grams for log in relevant_nutrition if log.fat_grams) / len(
            relevant_nutrition
        )

        # 9. Pack results
        res_pack = {
            "tdee": tdee,
            "conf_data": conf_data,
            "avg_cal": avg_calories_logged,
            "avg_p": avg_protein,
            "avg_c": avg_carbs,
            "avg_f": avg_fat,
            "weekly_chg": weekly_change,
            "energy": energy_balance,
            "status": status,
            "is_stable": is_stable,
            "relevant_nut": relevant_nutrition,
            "p_start": period_start,
            "p_end": period_end,
            "s_weight": start_weight,
            "e_weight": end_weight,
            "lat_weight": actual_latest_weight,
            "target": daily_target,
            "g_rate": goal_rate,
            "g_type": goal_type,
            "profile": profile,
            "w_goal": weeks_to_goal,
            "g_eta": goal_eta_weeks,
            "out_cnt": outliers_count,
            "w_logs": weight_logs,
            "adh_rate": adherence_rate,
            "w_logs_raw": weight_logs_raw,
            "n_logs": nutrition_logs,
        }
        result = self._map_result(res_pack)
        if comp_changes:
            result.update(comp_changes)
        if weight_logs[-1].bmr:
            result["scale_bmr"] = weight_logs[-1].bmr

        # Persist coaching check-in data
        if profile and daily_target != profile.tdee_last_target:
            self.db.update_user_coaching_target(
                user_email, daily_target, date.today().isoformat()
            )

        return result

    def get_current_targets(self, user_email: str) -> dict:
        """
        Retrieves current TDEE and daily calorie targets for a user.
        Uses coaching check-in logic for daily_target calculation.
        """
        tdee_data = self.calculate_tdee(user_email)
        tdee = tdee_data.get("tdee", 2000)
        daily_target = tdee_data.get("daily_target", tdee)

        profile = self.db.get_user_profile(user_email)
        reason = "Maintenance"
        goal_type = "maintain"

        if profile:
            goal_type = profile.goal_type
            if goal_type == "lose":
                reason = "Weight loss (coaching check-in)"
            elif goal_type == "gain":
                reason = "Weight gain (coaching check-in)"

        return {
            "tdee": tdee,
            "daily_target": int(round(daily_target)),
            "reason": reason,
            "goal_type": goal_type,
        }

    def _map_result(self, p: dict) -> dict:
        """Helper to map results to the final dictionary."""
        macro_targets = self._calculate_macro_targets(p["target"], p["lat_weight"])
        stability = self._calculate_stability_score(p["target"], p["relevant_nut"])

        return {
            "tdee": int(round(p["tdee"])),
            "confidence": p["conf_data"]["level"],
            "confidence_reason": p["conf_data"]["reason"],
            "avg_calories": int(round(p["avg_cal"])),
            "avg_protein": int(round(p["avg_p"])),
            "avg_carbs": int(round(p["avg_c"])),
            "avg_fat": int(round(p["avg_f"])),
            "weight_change_per_week": round(p["weekly_chg"], 2),
            "energy_balance": round(p["energy"], 1),
            "status": p["status"],
            "is_stable": p["is_stable"],
            "logs_count": len(p["relevant_nut"]),
            "nutrition_logs_count": len(p["relevant_nut"]),
            "startDate": p["p_start"].isoformat(),
            "endDate": p["p_end"].isoformat(),
            "start_weight": round(p["s_weight"], 2),
            "end_weight": round(p["e_weight"], 2),
            "latest_weight": p["lat_weight"],
            "daily_target": p["target"],
            "goal_weekly_rate": p["g_rate"],
            "goal_type": p["g_type"],
            "target_weight": p["profile"].target_weight if p["profile"] else None,
            "weeks_to_goal": p["w_goal"],
            "goal_eta_weeks": p["g_eta"],
            "outliers_count": p["out_cnt"],
            "weight_logs_count": len(p["w_logs"]),
            "weight_trend": [
                {
                    "date": log.date.isoformat() if isinstance(log.date, date) else log.date,
                    "weight": log.weight_kg,
                    "trend": round(log.trend_weight, 2) if log.trend_weight else None,
                }
                for log in p["w_logs"]
            ],
            "expenditure_trend": "stable",
            "consistency_score": int(round(p["adh_rate"] * 100)),
            "macro_targets": macro_targets,
            "stability_score": stability,
            "consistency": [
                {
                    "date": (date.today() - timedelta(days=i)).isoformat(),
                    "weight": (date.today() - timedelta(days=i))
                    in {log.date for log in p["w_logs_raw"]},
                    "nutrition": (date.today() - timedelta(days=i))
                    in {
                        (log.date.date() if isinstance(log.date, datetime) else log.date)
                        for log in p["n_logs"]
                    },
                }
                for i in range(27, -1, -1)
            ],
            "calorie_trend": [
                {
                    "date": (p["p_start"] + timedelta(days=i)).isoformat(),
                    "calories": next(
                        (
                            log_item.calories
                            for log_item in p["relevant_nut"]
                            if (
                                log_item.date.date()
                                if isinstance(log_item.date, datetime)
                                else log_item.date
                            )
                            == (p["p_start"] + timedelta(days=i))
                        ),
                        0,
                    ),
                }
                for i in range((p["p_end"] - p["p_start"]).days + 1)
            ],
        }

    def _calculate_body_composition_changes(self, logs: List[WeightLog]) -> dict | None:
        """Calculate fat and muscle mass changes using actual scale data."""
        valid_logs = [log for log in logs if log.body_fat_pct is not None]
        if len(valid_logs) < 2:
            return None

        first, last = valid_logs[0], valid_logs[-1]
        fat_mass_start = first.weight_kg * (cast(float, first.body_fat_pct) / 100.0)
        fat_mass_end = last.weight_kg * (cast(float, last.body_fat_pct) / 100.0)
        fat_change = fat_mass_end - fat_mass_start

        muscle_change = None
        # Priority: muscle_mass_kg -> muscle_mass_pct -> fallback (LBM change)
        if first.muscle_mass_kg is not None and last.muscle_mass_kg is not None:
            muscle_change = last.muscle_mass_kg - first.muscle_mass_kg
        elif first.muscle_mass_pct and last.muscle_mass_pct:
            m_start = first.weight_kg * (first.muscle_mass_pct / 100.0)
            m_end = last.weight_kg * (last.muscle_mass_pct / 100.0)
            muscle_change = m_end - m_start
        else:
            muscle_change = (last.weight_kg - first.weight_kg) - fat_change

        return {
            "fat_change_kg": round(fat_change, 2),
            "muscle_change_kg": round(muscle_change, 2),
            "start_fat_pct": round(cast(float, first.body_fat_pct), 2),
            "end_fat_pct": round(cast(float, last.body_fat_pct), 2),
            "start_muscle_pct": round(cast(float, first.muscle_mass_pct), 2)
            if first.muscle_mass_pct
            else (round(first.muscle_mass_kg / first.weight_kg * 100, 2) if first.muscle_mass_kg else None),
            "end_muscle_pct": round(cast(float, last.muscle_mass_pct), 2)
            if last.muscle_mass_pct
            else (round(last.muscle_mass_kg / last.weight_kg * 100, 2) if last.muscle_mass_kg else None),
            "start_muscle_kg": round(first.muscle_mass_kg, 2) if first.muscle_mass_kg else None,
            "end_muscle_kg": round(last.muscle_mass_kg, 2) if last.muscle_mass_kg else None,
        }

    # pylint: disable=too-many-locals
    def _calculate_regression_trend(
        self, logs: List[WeightLog]
    ) -> tuple[float, float, float]:
        """Calculates linear regression trend of weight logs."""
        if not logs:
            return 0.0, 0.0, 0.0
        start_date = logs[0].date
        x_list, y_list = [], []
        for log in logs:
            x_list.append((log.date - start_date).days)
            y_list.append(log.weight_kg)
        if len(x_list) < 2:
            return 0.0, y_list[0], 0.0
        try:
            x_arr, y_arr = np.array(x_list), np.array(y_list)
            weights = np.exp([-0.10 * (x_list[-1] - d) for d in x_list])
            m, c = np.polyfit(x_arr, y_arr, 1, w=weights)
            if np.std(y_arr) == 0 or np.std(x_arr) == 0:
                r_val = 0.0
            else:
                r_val = np.corrcoef(x_arr, y_arr)[0, 1]
            return float(m), float(c), float(r_val)
        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error("Regression calculation failed: %s", e)
            total_days = x_list[-1] - x_list[0]
            slope = (y_list[-1] - y_list[0]) / total_days if total_days > 0 else 0.0
            return slope, y_list[0], 0.0

    def _calculate_confidence(self, days_elapsed, nutrition_count, expected):
        """Determines confidence level and reason."""
        adherence = nutrition_count / expected if expected > 0 else 0
        if days_elapsed < 14:
            return {
                "level": "low",
                "reason": f"Histórico curto ({days_elapsed} dias). Mínimo: 14.",
            }
        if adherence > 0.85:
            return {"level": "high", "reason": "Excelente consistência de dados!"}
        if adherence > 0.6:
            return {
                "level": "medium",
                "reason": f"Aderência parcial ({adherence * 100:.0f}%).",
            }
        return {
            "level": "low",
            "reason": f"Muitos gaps nos registros ({adherence * 100:.0f}%).",
        }

    def _calculate_fallback_tdee(self, user_email, weight_logs, nutrition_logs) -> dict:
        """Safe TDEE estimate when adaptive data is missing."""
        profile = self.db.get_user_profile(user_email)
        latest_weight = (
            sorted(weight_logs, key=lambda x: x.date)[-1].weight_kg
            if weight_logs
            else 70.0
        )
        scale_bmr = next((log.bmr for log in reversed(weight_logs) if log.bmr), None)
        calc_bmr = 0.0
        if profile and profile.height and profile.age:
            try:
                adj = -161 if profile.gender in ("Feminino", "female") else 5
                calc_bmr = (
                    (10 * latest_weight)
                    + (6.25 * profile.height)
                    - (5 * profile.age)
                    + adj
                )
            # pylint: disable=broad-exception-caught
            except Exception:
                pass
        base_bmr = scale_bmr or calc_bmr or (latest_weight * 22) or 1500
        tdee_est = base_bmr * 1.35
        days = (
            (weight_logs[-1].date - weight_logs[0].date).days
            if weight_logs and len(weight_logs) >= 2
            else 7
        )
        adh = len(nutrition_logs) / (days + 1) if days > 0 else 0
        target, goal_type, goal_rate = int(round(tdee_est)), "maintain", 0.0
        if profile:
            goal_type, goal_rate = profile.goal_type, profile.weekly_rate or 0.0
            adj = (
                -1 * abs(goal_rate) * 1100
                if goal_type == "lose"
                else abs(goal_rate) * 1100
                if goal_type == "gain"
                else 0
            )
            target = max(1000, int(round(tdee_est + adj)))
        res = {
            "tdee": int(round(tdee_est)),
            "confidence": "none",
            "avg_calories": int(
                round(sum(n.calories for n in nutrition_logs) / len(nutrition_logs))
            )
            if nutrition_logs
            else 0,
            "weight_change_per_week": 0.0,
            "status": "maintenance",
            "is_stable": True,
            "logs_count": len(nutrition_logs),
            "nutrition_logs_count": len(nutrition_logs),
            "startDate": weight_logs[0].date.isoformat()
            if weight_logs
            else date.today().isoformat(),
            "endDate": weight_logs[-1].date.isoformat()
            if weight_logs
            else date.today().isoformat(),
            "latest_weight": latest_weight,
            "daily_target": target,
            "goal_weekly_rate": goal_rate,
            "goal_type": goal_type,
            "consistency_score": int(round(adh * 100)),
            "macro_targets": self._calculate_macro_targets(target, latest_weight),
            "weight_trend": [],
            "consistency": [],
            "calorie_trend": [],
            "confidence_reason": "Utilizando estimativa baseada em seu metabolismo basal (BMR) "
            "devido a histórico de dados insuficiente ou instável.",
        }
        comp = self._calculate_body_composition_changes(weight_logs)
        if comp:
            res.update(comp)
        return res

    def _calculate_macro_targets(self, daily_target: int, weight_kg: float) -> dict:
        """
        Calculates macro targets ensuring total calories = daily_target.

        Strategy:
        1. Protein: 1.6-2.0g per kg, but capped to max 40% of daily target
        2. Fat: 25-30% of daily target
        3. Carbs: Remaining calories

        This prevents macro totals from exceeding the daily target in extreme cases
        (e.g., high weight + low calorie target).
        """
        # Step 1: Calculate ideal protein (1.8g per kg of body weight)
        ideal_protein_g = weight_kg * 1.8
        protein_kcal_max = daily_target * 0.40  # Cap at 40% of target
        ideal_protein_g = min(ideal_protein_g, protein_kcal_max / 4)  # Convert to grams
        protein_g = int(round(ideal_protein_g))
        protein_kcal = protein_g * 4

        # Step 2: Calculate fat (27% of daily target - middle of 25-30% range)
        fat_kcal = daily_target * 0.27
        fat_g = int(round(fat_kcal / 9))
        fat_kcal = fat_g * 9  # Recalculate based on rounded grams

        # Step 3: Carbs get the remainder
        remaining_kcal = daily_target - protein_kcal - fat_kcal
        carb_g = int(round(max(0, remaining_kcal / 4)))

        return {"protein": protein_g, "carbs": carb_g, "fat": fat_g}

    def _calculate_stability_score(
        self, target: int, nutrition_logs: list[NutritionLog]
    ) -> int:
        """Calculates consistency score."""
        if not nutrition_logs or target <= 0:
            return 0
        last_7 = sorted(nutrition_logs, key=lambda x: x.date, reverse=True)[:7]
        if not last_7:
            return 0
        stable = sum(
            1 for log in last_7 if abs(log.calories - target) <= (target * 0.10)
        )
        return int(round((stable / len(last_7)) * 100))

    def _calculate_coaching_target(
        self,
        tdee: float,
        avg_calories: float,
        weekly_change: float,
        profile: "UserProfile | None",
    ) -> int:
        """
        Calculates daily_target using MacroFactor-inspired approach.

        v2 changes:
        - NO off-track penalty (adherence-neutral)
        - The adaptive TDEE naturally adjusts if user isn't progressing
        - Gradual adjustment applied separately via _apply_gradual_adjustment()

        Logic:
        1. If no profile or goal=maintain: return TDEE
        2. Calculate ideal_target = TDEE ± deficit/surplus for goal_rate
        3. Apply gradual adjustment (max ±100 kcal/week vs previous target)
        4. Apply safety floor (gender min + max 30% deficit)
        """
        if not profile or profile.goal_type == "maintain":
            return int(round(tdee))

        goal_rate = abs(profile.weekly_rate or 0.0)

        # Calculate ideal target based on goal — NO penalty for being off-track
        if profile.goal_type == "lose":
            deficit_needed = goal_rate * 1100
            ideal_target = int(round(tdee - deficit_needed))
        else:  # gain
            surplus_needed = goal_rate * 1100
            ideal_target = int(round(tdee + surplus_needed))

        # Apply gradual adjustment
        ideal_target = self._apply_gradual_adjustment(ideal_target, profile)

        # Apply safety floor
        ideal_target = self._apply_safety_floor(ideal_target, tdee, profile)

        return ideal_target

    def _apply_gradual_adjustment(
        self, ideal_target: int, profile: "UserProfile | None"
    ) -> int:
        """
        Caps target changes to ±MAX_WEEKLY_ADJUSTMENT kcal per check-in interval.
        """
        if not profile:
            return ideal_target

        prev_target = profile.tdee_last_target
        last_check_in = profile.tdee_last_check_in

        # First time: no previous target to cap against
        if prev_target is None or not isinstance(prev_target, int):
            return ideal_target

        # Check if enough time has passed since last check-in
        today = date.today()
        if last_check_in and isinstance(last_check_in, str):
            try:
                last_date = date.fromisoformat(last_check_in)
                if (today - last_date).days < self.CHECK_IN_INTERVAL_DAYS:
                    return prev_target  # Too soon, no change
            except (ValueError, TypeError):
                pass

        # Apply ±100 kcal cap
        diff = ideal_target - prev_target
        if abs(diff) <= self.MAX_WEEKLY_ADJUSTMENT:
            return ideal_target
        step = self.MAX_WEEKLY_ADJUSTMENT if diff > 0 else -self.MAX_WEEKLY_ADJUSTMENT
        return prev_target + step

    def _apply_safety_floor(
        self, target: int, tdee: float, profile: "UserProfile | None"
    ) -> int:
        """
        Applies gender-specific calorie floor and max deficit percentage.
        Three safety checks (highest floor wins):
        1. Gender minimum: 1200 (female) / 1500 (male)
        2. Max deficit: never exceed 30% below TDEE
        3. Absolute minimum: 1200 kcal (generic)
        """
        if not profile:
            return max(self.MIN_TDEE, target)

        # Gender-specific minimum
        is_female = profile.gender in ("Feminino", "female")
        gender_min = self.MIN_CALORIES_FEMALE if is_female else self.MIN_CALORIES_MALE

        # Max deficit percentage (only for deficit goals)
        if profile.goal_type == "lose":
            min_by_deficit = int(round(tdee * (1 - self.MAX_DEFICIT_PCT)))
            return max(gender_min, min_by_deficit, target)

        # For gain/maintain, only gender floor applies
        return max(gender_min, target)
