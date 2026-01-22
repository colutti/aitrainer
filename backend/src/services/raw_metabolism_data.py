from datetime import date, timedelta, datetime
from typing import List

from src.services.database import MongoDatabase
from src.api.models.weight_log import WeightLog
from src.api.models.nutrition_log import NutritionLog
from src.api.models.raw_metabolism_data import RawMetabolismData, AnalysisPeriod


class RawMetabolismDataService:
    """
    Service responsible for collecting and formatting RAW metabolism data
    for AI analysis, without pre-calculating metrics.
    """

    def __init__(self, db: MongoDatabase):
        self.db = db

    def get_raw_data_for_insight(
        self, user_email: str, lookback_weeks: int = 3
    ) -> RawMetabolismData:
        """
        Collects raw weight and nutrition logs for the specified period.

        Args:
            user_email: The user's email.
            lookback_weeks: Number of weeks to look back (default 3).

        Returns:
            Dict containing:
            - weight_logs: List of WeightLog objects
            - nutrition_logs: List of NutritionLog objects
            - user_profile: UserProfile object (or dict)
            - period: Dict with start_date and end_date
        """
        end_date = date.today()
        start_date = end_date - timedelta(weeks=lookback_weeks)

        # 1. Fetch Raw Data
        weight_logs = self.db.get_weight_logs_by_date_range(
            user_email, start_date, end_date
        )

        # Nutrition logs require datetime for the query, usually
        nutrition_logs = self.db.get_nutrition_logs_by_date_range(
            user_email,
            datetime(start_date.year, start_date.month, start_date.day),
            datetime(end_date.year, end_date.month, end_date.day),
        )

        profile = self.db.get_user_profile(user_email)

        # Sort logs by date ascending
        weight_logs.sort(key=lambda x: x.date)
        nutrition_logs.sort(key=lambda x: x.date)

        return RawMetabolismData(
            weight_logs=weight_logs,
            nutrition_logs=nutrition_logs,
            user_profile=profile,
            period=AnalysisPeriod(start_date=start_date, end_date=end_date),
        )

    def format_weight_logs_table(self, logs: List[WeightLog]) -> str:
        """Formats weight logs into a Markdown table."""
        if not logs:
            return "_Nenhuma pesagem registrada no período._"

        table = "| Data | Peso | %Gord | %Musc | %Água | Visc | BMR | Fonte |\n"
        table += "|---|---|---|---|---|---|---|---|\n"

        for log in logs:
            date_str = log.date.strftime("%d/%m")
            weight = f"{log.weight_kg}"
            fat = f"{log.body_fat_pct}" if log.body_fat_pct else "-"
            muscle = f"{log.muscle_mass_pct}" if log.muscle_mass_pct else "-"
            water = f"{log.body_water_pct}" if log.body_water_pct else "-"
            visc = f"{log.visceral_fat}" if log.visceral_fat else "-"
            bmr = f"{log.bmr}" if log.bmr else "-"
            source = log.source if log.source else "manual"

            table += f"| {date_str} | {weight} | {fat} | {muscle} | {water} | {visc} | {bmr} | {source} |\n"

        return table

    def format_nutrition_logs_table(self, logs: List[NutritionLog]) -> str:
        """Formats nutrition logs into a Markdown table."""
        if not logs:
            return "_Nenhuma dieta registrada no período._"

        table = "| Data | Kcal | Prot | Carbs | Gord | Fibra |\n"
        table += "|---|---|---|---|---|---|\n"

        for log in logs:
            date_str = log.date.strftime("%d/%m")
            kcal = f"{log.calories}"
            prot = f"{int(round(log.protein_grams))}"
            carbs = f"{int(round(log.carbs_grams))}"
            fat = f"{int(round(log.fat_grams))}"
            fiber = f"{log.fiber_grams}" if log.fiber_grams else "-"

            table += f"| {date_str} | {kcal} | {prot} | {carbs} | {fat} | {fiber} |\n"

        return table
