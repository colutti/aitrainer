#!/usr/bin/env python3
"""
Script to import body composition data from scale CSV export.

Usage:
  python scripts/import_scale_data.py USER_EMAIL path/to/BODY.csv [--dry-run]

Column Mapping (auto-detected):
  - time -> date
  - weight -> weight_kg
  - fatRate -> body_fat_pct
  - muscleRate -> muscle_mass_pct
  - boneMass -> bone_mass_kg
  - bodyWaterRate -> body_water_pct
  - visceralFat -> visceral_fat
  - metabolism -> bmr
  - bmi -> bmi
"""
import argparse
import csv
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")

try:
    from src.core.config import settings
    from src.api.models.weight_log import WeightLog
    from src.services.database import MongoDatabase
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)

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

def parse_scale_csv(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Parse scale CSV and aggregate by date.
    Keeps the last entry for each day.
    
    Returns:
        Dict mapping date string (YYYY-MM-DD) to log data dict.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    daily_data: Dict[str, Dict[str, Any]] = {}
    
    with open(file_path, 'r', encoding='utf-8-sig') as f:
        # Strip potential BOM or whitespace from fieldnames
        reader = csv.DictReader(f)
        reader.fieldnames = [name.strip().lstrip('\ufeff') for name in reader.fieldnames] if reader.fieldnames else []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                # Map columns
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
                            val = val[:10]
                        else:
                            # Try parsing numbers
                            try:
                                if model_field in ["visceral_fat", "bmr"]:
                                    val = int(float(val))
                                else:
                                    val = float(val)
                            except ValueError:
                                continue
                                
                        data[model_field] = val
                
                if "date" not in data or "weight_kg" not in data:
                    print(f"  ⚠️  Line {row_num}: Missing date or weight, skipping.")
                    continue
                
                date_str = data["date"]
                
                # Logic: If we already have data for this day, should we overwrite?
                # Yes, assume latest in file (or latest time) is most accurate/final.
                # However, if current row has missing composition data (nulls), 
                # but existing data HAS composition, keep existing composition.
                
                existing = daily_data.get(date_str, {})
                
                # Check if current row has composition data
                has_comp = "body_fat_pct" in data
                existing_has_comp = "body_fat_pct" in existing
                
                if has_comp or not existing_has_comp:
                    # Overwrite if we have better data, or if we just want to update weight
                    # Merge with existing to keep other fields if needed? 
                    # Simpler to just take the new row if it has composition.
                    daily_data[date_str] = data
                elif existing_has_comp and not has_comp:
                    # If we simply update weight but lose composition, maybe we should update ONLY weight?
                    # The user requirement said: "Rows with null composition fields will still import weight".
                    # But for same day, we want "last complete reading".
                    # Let's assume the user weighs multiple times.
                    # Ideally we parse full datetime to sort. 
                    # But for now, simple logic: prefer row with fat %.
                    pass 

            except Exception as e:
                print(f"  ⚠️  Line {row_num}: Error processing - {e}")
                continue
                
    return daily_data

def import_scale_data(user_email: str, csv_path: str, dry_run: bool = False):
    print(f"\n📊 Importing scale data for: {user_email}")
    print(f"📁 File: {csv_path}")
    
    # Safety confirm always
    confirm_execution(
        "Import Scale Data", 
        {"user": user_email, "csv": csv_path, "dry_run": dry_run}
    )

    print("Parsing CSV...")
    try:
        daily_data = parse_scale_csv(csv_path)
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return

    print(f"✅ Found {len(daily_data)} days of data\n")
    
    if not daily_data:
        print("❌ No valid data found.")
        return

    db = None
    if not dry_run:
        db = MongoDatabase()
        if not db.get_user_profile(user_email):
             print(f"❌ User '{user_email}' not found.")
             return
        print(f"✅ User validated\n")

    created = 0
    updated = 0
    
    print("=" * 80)
    print(f"{'Date':<12} {'Weight':>8} {'Fat %':>8} {'Muscle %':>8} {'BMR':>6} {'Status'}")
    print("=" * 80)
    
    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]
        
        # Prepare WeightLog
        try:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            log = WeightLog(
                user_email=user_email,
                date=log_date,
                **{k: v for k, v in data.items() if k != "date"},
                source="scale_import"
            )
            
            status = "preview"
            if not dry_run:
                doc_id, is_new = db.save_weight_log(log)
                if is_new:
                    created += 1
                    status = "created ✓"
                else:
                    updated += 1
                    status = "updated ↻"
            
            fat_display = f"{log.body_fat_pct:.1f}%" if log.body_fat_pct else "-"
            muscle_display = f"{log.muscle_mass_pct:.1f}%" if log.muscle_mass_pct else "-"
            bmr_display = str(log.bmr) if log.bmr else "-"
            
            print(f"{date_str:<12} {log.weight_kg:>6.1f}kg {fat_display:>8} {muscle_display:>8} {bmr_display:>6} {status}")
            
        except Exception as e:
            print(f"{date_str:<12} ERROR: {e}")
            
    print("=" * 80)
    print(f"\n📈 Summary:")
    print(f"   Total days: {len(daily_data)}")
    if not dry_run:
        print(f"   New records: {created}")
        print(f"   Updated: {updated}")
    else:
        print("   (dry-run mode - no changes)")

def main():
    parser = argparse.ArgumentParser(description="Import scale data from CSV.")
    parser.add_argument("user_email", help="User email")
    parser.add_argument("csv_path", help="Path to CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    
    args = parser.parse_args()
    
    import_scale_data(args.user_email, args.csv_path, args.dry_run)

if __name__ == "__main__":
    main()
