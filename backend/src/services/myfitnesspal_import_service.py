import csv
import io
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

from src.api.models.nutrition_log import NutritionLog
from src.api.models.import_result import ImportResult
from src.services.database import MongoDatabase


# CSV Column Mapping (Portuguese MyFitnessPal headers → internal names)
COLUMN_MAPPING = {
    "Data": "date",
    "Refeição": "meal",
    "Calorias": "calories",
    "Gorduras (g)": "fat",
    "Colesterol": "cholesterol",
    "Sódio (mg)": "sodium",
    "Carboidratos (g)": "carbs",
    "Fibra": "fiber",
    "Açucar": "sugar",
    "Proteínas (g)": "protein",
}

REQUIRED_COLUMNS = ["Data", "Calorias", "Gorduras (g)", "Carboidratos (g)", "Proteínas (g)"]


@dataclass
class DailyNutrition:
    """Aggregated daily nutrition from multiple meals."""
    date: datetime
    calories: float = 0.0
    protein: float = 0.0
    carbs: float = 0.0
    fat: float = 0.0
    fiber: Optional[float] = None
    sugar: Optional[float] = None
    sodium: Optional[float] = None
    cholesterol: Optional[float] = None
    meals: list = field(default_factory=list)

    def add_meal(self, meal_name: str, row: dict) -> None:
        """Add a meal's nutrition to the daily total."""
        self.meals.append(meal_name)
        self.calories += float(row.get("calories", 0) or 0)
        self.protein += float(row.get("protein", 0) or 0)
        self.carbs += float(row.get("carbs", 0) or 0)
        self.fat += float(row.get("fat", 0) or 0)
        
        # Optional fields - accumulate only if present
        if row.get("fiber"):
            self.fiber = (self.fiber or 0) + float(row["fiber"])
        if row.get("sugar"):
            self.sugar = (self.sugar or 0) + float(row["sugar"])
        if row.get("sodium"):
            self.sodium = (self.sodium or 0) + float(row["sodium"])
        if row.get("cholesterol"):
            self.cholesterol = (self.cholesterol or 0) + float(row["cholesterol"])

    def to_nutrition_log(self, user_email: str) -> NutritionLog:
        """Convert to NutritionLog model."""
        return NutritionLog(
            user_email=user_email,
            date=self.date,
            calories=int(round(self.calories)),
            protein_grams=round(self.protein, 1),
            carbs_grams=round(self.carbs, 1),
            fat_grams=round(self.fat, 1),
            fiber_grams=round(self.fiber, 1) if self.fiber else None,
            sugar_grams=round(self.sugar, 1) if self.sugar else None,
            sodium_mg=round(self.sodium, 1) if self.sodium else None,
            cholesterol_mg=round(self.cholesterol, 1) if self.cholesterol else None,
            source="myfitnesspal",
            notes=f"Importado do MyFitnessPal ({len(self.meals)} refeições)"
        )


def parse_csv_content(file_content: str) -> dict[str, DailyNutrition]:
    """
    Parse MyFitnessPal CSV content and aggregate by date.
    
    Args:
        file_content: Raw CSV string content.
        
    Returns:
        Dictionary mapping date strings to DailyNutrition objects.
    """
    daily_data: dict[str, DailyNutrition] = {}
    
    # Handle both \n and \r\n line endings
    f = io.StringIO(file_content, newline=None)
    reader = csv.DictReader(f)
    
    # Validate required columns
    headers = reader.fieldnames or []
    missing = [col for col in REQUIRED_COLUMNS if col not in headers]
    if missing:
        raise ValueError(f"Colunas obrigatórias ausentes: {', '.join(missing)}. Verifique se o CSV é do MyFitnessPal em português.")
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
        try:
            # Normalize column names
            normalized = {}
            for orig_col, internal_name in COLUMN_MAPPING.items():
                if orig_col in row:
                    normalized[internal_name] = row[orig_col]
            
            date_str = normalized.get("date", "").strip()
            if not date_str:
                continue
            
            # Parse date
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # Try explicit skip of malformed dates silently to avoid log spam, 
                # or we could log/track errors if needed.
                continue
            
            # Get or create daily aggregation
            if date_str not in daily_data:
                daily_data[date_str] = DailyNutrition(date=date_obj)
            
            meal_name = normalized.get("meal", "Refeição")
            daily_data[date_str].add_meal(meal_name, normalized)
            
        except Exception:
            # Skip rows with errors
            continue

    return daily_data


def import_nutrition_from_csv(
    user_email: str, 
    csv_content: str, 
    db: MongoDatabase
) -> ImportResult:
    """
    Import nutrition data from MyFitnessPal CSV content.
    
    Args:
        user_email: User's email address.
        csv_content: Raw CSV string content.
        db: Database instance.
        
    Returns:
        ImportResult object with counts.
    """
    try:
        daily_data = parse_csv_content(csv_content)
    except ValueError as e:
        # Re-raise validation errors
        raise e
    except Exception as e:
        raise ValueError(f"Erro ao processar CSV: {str(e)}")

    if not daily_data:
        return ImportResult(created=0, updated=0, errors=0, total_days=0)
    
    created = 0
    updated = 0
    errors = 0
    error_messages = []
    
    sorted_dates = sorted(daily_data.keys())
    
    for date_str in sorted_dates:
        daily = daily_data[date_str]
        log = daily.to_nutrition_log(user_email)
        
        try:
            _, is_new = db.save_nutrition_log(log)
            if is_new:
                created += 1
            else:
                updated += 1
        except Exception as e:
            errors += 1
            error_messages.append(f"Erro em {date_str}: {str(e)}")
            
    return ImportResult(
        created=created,
        updated=updated,
        errors=errors,
        total_days=len(daily_data),
        error_messages=error_messages
    )
