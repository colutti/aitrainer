"""
Pydantic models for nutrition logging.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NutritionLog(BaseModel):
    """
    Represents a daily nutrition log for a user.

    Attributes:
        user_email: Email of the user.
        date: Date of the log.
        calories: Total calories consumed.
        protein_grams: Total protein in grams.
        carbs_grams: Total carbohydrates in grams.
        fat_grams: Total fat in grams.
        fiber_grams: Total fiber in grams (optional).
        sugar_grams: Total sugar in grams (optional).
        sodium_mg: Total sodium in mg (optional).
        cholesterol_mg: Total cholesterol in mg (optional).
        source: Source of the data (e.g., "chat", "manual", "myfitnesspal").
        notes: Optional notes about the day.
    """

    user_email: str = Field(..., description="Email do usuário")
    date: datetime = Field(default_factory=datetime.now, description="Data do registro")
    
    # Main macros
    calories: int = Field(..., ge=0, description="Calorias totais")
    protein_grams: float = Field(..., ge=0, description="Proteínas (g)")
    carbs_grams: float = Field(..., ge=0, description="Carboidratos (g)")
    fat_grams: float = Field(..., ge=0, description="Gorduras (g)")
    
    # Micros (Optional)
    fiber_grams: Optional[float] = Field(None, ge=0, description="Fibras (g)")
    sugar_grams: Optional[float] = Field(None, ge=0, description="Açúcar (g)")
    sodium_mg: Optional[float] = Field(None, ge=0, description="Sódio (mg)")
    cholesterol_mg: Optional[float] = Field(None, ge=0, description="Colesterol (mg)")
    
    source: str = Field(default="chat", description="Origem dos dados")
    notes: Optional[str] = Field(None, description="Notas opcionais")


class NutritionWithId(NutritionLog):
    """Nutrition log with MongoDB ID for API responses."""
    id: str = Field(..., description="ID do log no MongoDB")
