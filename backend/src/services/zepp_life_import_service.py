import csv
import io
from datetime import datetime
from typing import Dict, Any
from src.api.models.weight_log import WeightLog
from src.api.models.import_result import ImportResult
from src.services.database import MongoDatabase
import logging

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

def parse_zepp_life_csv(file_content: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse Zepp Life CSV content and aggregate by date.
    Keeps the last entry for each day, prioritizing entries with body composition data.
    
    Args:
        file_content: Raw CSV string content.
        
    Returns:
        Dict mapping date string (YYYY-MM-DD) to log data dict.
    """
    daily_data: Dict[str, Dict[str, Any]] = {}
    
    # Handle both \n and \r\n line endings
    f = io.StringIO(file_content, newline=None)
    
    # Strip potential BOM or whitespace from fieldnames if present
    # logic similar to original script but adapted for StringIO
    reader = csv.DictReader(f)
    if reader.fieldnames:
        reader.fieldnames = [name.strip().lstrip('\ufeff') for name in reader.fieldnames]
    
    for row_num, row in enumerate(reader, start=2):
        try:
            data = {}
            for csv_col, model_field in COLUMN_MAPPING.items():
                if csv_col in row:
                    val = row[csv_col]
                    # Handle null/empty
                    if not val or val.lower() == 'null':
                        continue
                        
                    # Parse date specially
                    if model_field == "date":
                        # Format: 2025-12-09 06:06:59+0000
                        # Take first 10 chars for YYYY-MM-DD
                        data[model_field] = val[:10]
                    else:
                        # Try parsing numbers
                        try:
                            if model_field in ["visceral_fat", "bmr"]:
                                data[model_field] = int(float(val))
                            else:
                                data[model_field] = float(val)
                        except ValueError:
                            continue
            
            if "date" not in data or "weight_kg" not in data:
                continue
            
            date_str = data["date"]
            
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
            elif existing_has_comp and not has_comp:
                # If we simply update weight but lose composition, we stick with the existing one
                # that has composition. (Simplification per original script logic)
                pass 

        except Exception as e:
            logger.warning(f"Error processing row {row_num}: {e}")
            continue
            
    return daily_data

def import_zepp_life_data(
    user_email: str, 
    csv_content: str, 
    db: MongoDatabase
) -> ImportResult:
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
        raise ValueError(f"Error parsing CSV: {str(e)}")

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
                **{k: v for k, v in data.items() if k != "date"},
                source="zepp_life_import"
            )
            
            doc_id, is_new = db.save_weight_log(log)
            if is_new:
                created += 1
            else:
                updated += 1
                
        except Exception as e:
            errors += 1
            error_messages.append(f"Error on {date_str}: {str(e)}")
            
    return ImportResult(
        created=created,
        updated=updated,
        errors=errors,
        total_days=len(daily_data),
        error_messages=error_messages
    )
