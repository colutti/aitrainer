"""
Pydantic models for nutrition statistics.
"""

from datetime import datetime
from pydantic import BaseModel, Field

from src.api.models.nutrition_log import NutritionWithId


class DailyMacros(BaseModel):
    """Simplified daily macro summary for charts."""

    date: datetime
    calories: int
    protein: float
    carbs: float
    fat: float


class NutritionStats(BaseModel):
    """Aggregated nutrition statistics for the dashboard."""

    today: NutritionWithId | None = Field(
        default=None, description="Log nutricional de hoje, se existir"
    )

    weekly_adherence: list[bool] = Field(
        ...,
        description="Lista de 7 bools indicando dias com log na última semana (Dom-Sáb ou Seg-Dom)",
    )

    last_7_days: list[DailyMacros] = Field(
        ..., description="Lista de macros dos últimos 7 dias para gráficos"
    )

    avg_daily_calories: float = Field(
        ..., description="Média de calorias diárias nos últimos 7 dias"
    )

    avg_daily_calories_14_days: float = Field(
        default=0.0, description="Média de calorias diárias nos últimos 14 dias"
    )

    avg_protein: float = Field(
        ..., description="Média de proteína diária (g) nos últimos 7 dias"
    )

    total_logs: int = Field(..., description="Total de dias registrados no histórico")

    tdee: int | None = Field(default=None, description="TDEE calculado adaptativamente")
    daily_target: int | None = Field(
        default=None, description="Meta calórica diária baseada no TDEE e objetivo"
    )
    macro_targets: dict | None = Field(default=None, description="Metas de macros")
    stability_score: int | None = Field(default=None, description="Score de estabilidade")
    last_14_days: list[DailyMacros] = Field(
        default_factory=list, description="Lista de macros dos últimos 14 dias"
    )
