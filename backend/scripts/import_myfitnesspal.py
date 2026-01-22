#!/usr/bin/env python3
"""
Script para importar dados de nutrição do MyFitnessPal.

O MyFitnessPal exporta dados por refeição. Este script agrega os valores
por dia para criar um NutritionLog diário no banco de dados.

Uso:
  python scripts/import_myfitnesspal.py USER_EMAIL path/to/Nutrition.csv [--dry-run]

Exemplos:
  # Preview sem salvar
  python scripts/import_myfitnesspal.py test@email.com ~/Downloads/Nutrition.csv --dry-run

  # Importar de fato
  python scripts/import_myfitnesspal.py test@email.com ~/Downloads/Nutrition.csv
"""

import argparse
import csv
import sys
import os
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")

try:
    from src.api.models.nutrition_log import NutritionLog
    from src.services.database import MongoDatabase
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)


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

REQUIRED_COLUMNS = [
    "Data",
    "Calorias",
    "Gorduras (g)",
    "Carboidratos (g)",
    "Proteínas (g)",
]


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
            notes=f"Importado do MyFitnessPal ({len(self.meals)} refeições: {', '.join(self.meals)})",
        )


def parse_csv(file_path: str) -> dict[str, DailyNutrition]:
    """
    Parse MyFitnessPal CSV and aggregate by date.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Dictionary mapping date strings to DailyNutrition objects.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    daily_data: dict[str, DailyNutrition] = {}

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        headers = reader.fieldnames or []
        missing = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            try:
                # Normalize column names
                normalized = {}
                for orig_col, internal_name in COLUMN_MAPPING.items():
                    if orig_col in row:
                        normalized[internal_name] = row[orig_col]

                date_str = normalized.get("date", "").strip()
                if not date_str:
                    print(f"  ⚠️  Linha {row_num}: Data vazia, pulando...")
                    continue

                # Parse date
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                except ValueError:
                    print(
                        f"  ⚠️  Linha {row_num}: Formato de data inválido '{date_str}', pulando..."
                    )
                    continue

                # Get or create daily aggregation
                if date_str not in daily_data:
                    daily_data[date_str] = DailyNutrition(date=date_obj)

                meal_name = normalized.get("meal", "Refeição")
                daily_data[date_str].add_meal(meal_name, normalized)

            except Exception as e:
                print(f"  ⚠️  Linha {row_num}: Erro ao processar - {e}")
                continue

    return daily_data


def import_nutrition(
    user_email: str, csv_path: str, dry_run: bool = False
) -> tuple[int, int, int]:
    """
    Import nutrition data from MyFitnessPal CSV.

    Args:
        user_email: User's email address.
        csv_path: Path to CSV file.
        dry_run: If True, only preview without saving.

    Returns:
        Tuple of (created_count, updated_count, error_count)
    """
    print(f"\n📊 Importando dados do MyFitnessPal para: {user_email}")
    print(f"📁 Arquivo: {csv_path}")
    if dry_run:
        print("🔍 MODO DRY-RUN: Nenhum dado será salvo\n")
    else:
        print()

    # Parse CSV
    print("Parsing CSV...")
    daily_data = parse_csv(csv_path)
    print(f"✅ Encontrados {len(daily_data)} dias de dados\n")

    if not daily_data:
        print("❌ Nenhum dado válido encontrado no CSV.")
        return 0, 0, 0

    # Safety confirm always
    confirm_execution(
        "Import MyFitnessPal Data",
        {"user": user_email, "csv": csv_path, "dry_run": dry_run},
    )

    # Connect to database (only if not dry-run)
    db = None
    if not dry_run:
        db = MongoDatabase()

        # Verify user exists
        user = db.get_user_profile(user_email)
        if not user:
            print(f"❌ Usuário '{user_email}' não encontrado no banco de dados.")
            return 0, 0, 0
        print(f"✅ Usuário validado: {user_email}\n")

    created = 0
    updated = 0
    errors = 0

    # Sort by date for consistent output
    sorted_dates = sorted(daily_data.keys())

    print("=" * 60)
    print(f"{'Data':<12} {'Kcal':>6} {'P(g)':>6} {'C(g)':>6} {'G(g)':>6} {'Status'}")
    print("=" * 60)

    for date_str in sorted_dates:
        daily = daily_data[date_str]
        log = daily.to_nutrition_log(user_email)

        status = ""
        if dry_run:
            status = "preview"
        else:
            try:
                doc_id, is_new = db.save_nutrition_log(log)
                if is_new:
                    created += 1
                    status = "criado ✓"
                else:
                    updated += 1
                    status = "atualizado ↻"
            except Exception as e:
                errors += 1
                status = f"erro: {e}"

        print(
            f"{date_str:<12} {int(log.calories):>6} {log.protein_grams:>6.1f} {log.carbs_grams:>6.1f} {log.fat_grams:>6.1f} {status}"
        )

    print("=" * 60)
    print("\n📈 Resumo:")
    print(f"   Total de dias: {len(daily_data)}")
    if not dry_run:
        print(f"   Novos registros: {created}")
        print(f"   Atualizados: {updated}")
        if errors:
            print(f"   Erros: {errors}")
    else:
        print("   (nenhum dado salvo - modo dry-run)")

    return created, updated, errors


def main():
    parser = argparse.ArgumentParser(
        description="Importa dados de nutrição do MyFitnessPal (CSV) para o banco de dados.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Preview sem salvar (dry-run)
  python import_myfitnesspal.py user@email.com ~/Downloads/Nutrition.csv --dry-run

  # Importar dados
  python import_myfitnesspal.py user@email.com ~/Downloads/Nutrition.csv

O CSV do MyFitnessPal contém dados por refeição. Este script agrega
automaticamente todas as refeições de cada dia em um único registro diário.
        """,
    )

    parser.add_argument("user_email", help="Email do usuário para associar os dados")
    parser.add_argument(
        "csv_path", help="Caminho para o arquivo CSV exportado do MyFitnessPal"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview dos dados sem salvar no banco"
    )

    args = parser.parse_args()

    try:
        created, updated, errors = import_nutrition(
            user_email=args.user_email, csv_path=args.csv_path, dry_run=args.dry_run
        )

        if errors > 0:
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
