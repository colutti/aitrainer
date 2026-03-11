"""
This module provides services for importing weight data from Zepp Life CSV exports.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Dict, Any, cast
from src.api.models.weight_log import WeightLog
from src.api.models.import_result import ImportResult
from src.services.database import MongoDatabase

logger = logging.getLogger(__name__)

# Column mapping from Zepp Life CSV export to internal WeightLog fields
COLUMN_MAPPING = {
    "time": "date",
    "weight": "weight_kg",
    "fatRate": "body_fat_pct",
    "muscleRate": "muscle_mass_pct",
    "boneMass": "bone_mass_kg",
    "bodyWaterRate": "body_water_pct",
    "visceralFat": "visceral_fat",
    "metabolism": "bmr",
    "bmi": "bmi",
}


def _process_csv_row(
    row: Dict[str, str], daily_data: Dict[str, Dict[str, float | int]]
) -> None:
    """Helper function to process a single CSV row."""
    date_str = None
    data: Dict[str, float | int] = {}

    for csv_col, model_field in COLUMN_MAPPING.items():
        if csv_col in row:
            val = row[csv_col]
            if not val or val.lower() == "null":
                continue

            if model_field == "date":
                date_str = val[:10]
            else:
                try:
                    if model_field in ["visceral_fat", "bmr"]:
                        data[model_field] = int(float(val))
                    else:
                        data[model_field] = float(val)
                except ValueError:
                    continue

    if not date_str or "weight_kg" not in data:
        return

    # Logic: If we already have data for this day, should we overwrite?
    # Yes, assume latest in file (or latest time) is most accurate/final.
    # However, if current row has missing composition data (nulls),
    # but existing data HAS composition, keep existing composition.

    existing = daily_data.get(date_str, {})

    # Check if current row has composition data (using body_fat_pct as proxy)
    has_comp = "body_fat_pct" in data
    existing_has_comp = "body_fat_pct" in existing

    if has_comp or not existing_has_comp:
        # Overwrite if we have better data, or if we just want to update weight
        daily_data[date_str] = data


def parse_zepp_life_csv(file_content: str) -> Dict[str, Dict[str, float | int]]:
    """
    Parse Zepp Life CSV content and aggregate by date.
    Keeps the last entry for each day, prioritizing entries with body composition data.

    Args:
        file_content: Raw CSV string content.

    Returns:
        Dict mapping date string (YYYY-MM-DD) to log data dict.
    """
    daily_data: Dict[str, Dict[str, float | int]] = {}

    # Handle both \n and \r\n line endings
    f = io.StringIO(file_content, newline=None)

    # Strip potential BOM or whitespace from fieldnames if present
    reader = csv.DictReader(f)
    if reader.fieldnames:
        reader.fieldnames = [
            name.strip().lstrip("\ufeff") for name in reader.fieldnames
        ]

    for row_num, row in enumerate(reader, start=2):
        try:
            _process_csv_row(row, daily_data)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Error processing row %d: %s", row_num, e)
            continue

    return daily_data


def import_zepp_life_data(
    user_email: str, csv_content: str, db: MongoDatabase
) -> ImportResult:
    # pylint: disable=duplicate-code
    """
    Import weight/body composition data from Zepp Life CSV content.

    Args:
        user_email: User's email address.
        csv_content: Raw CSV string content.
        db: Database instance.

    Returns:
        ImportResult object with counts.
    """
    try:
        daily_data = parse_zepp_life_csv(csv_content)
    except Exception as e:
        raise ValueError(f"Error parsing CSV: {str(e)}") from e

    if not daily_data:
        return ImportResult(created=0, updated=0, errors=0, total_days=0)

    created = 0
    updated = 0
    errors = 0
    error_messages = []

    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]

        try:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            log = WeightLog(
                user_email=user_email,
                date=log_date,
                source="zepp_life_import",
                **cast(Dict[str, Any], data),
            )

            _, is_new = db.save_weight_log(log)
            if is_new:
                created += 1
            else:
                updated += 1

        except Exception as e:  # pylint: disable=broad-exception-caught
            errors += 1
            error_messages.append(f"Error on {date_str}: {str(e)}")

    return ImportResult(
        created=created,
        updated=updated,
        errors=errors,
        total_days=len(daily_data),
        error_messages=error_messages,
    )
