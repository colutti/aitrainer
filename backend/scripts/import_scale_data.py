#!/usr/bin/env python3
"""
Script to import body composition data from scale CSV export.
Refactored to use shared Zepp Life import service.

Usage:
  python scripts/import_scale_data.py USER_EMAIL path/to/BODY.csv [--dry-run]
"""

import argparse
import sys
import os
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core")

try:
    from src.api.models.weight_log import WeightLog
    from src.services.database import MongoDatabase
    from scripts.utils import confirm_execution
    from src.services.zepp_life_import_service import parse_zepp_life_csv
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)


def import_scale_data(user_email: str, csv_path: str, dry_run: bool = False):
    print(f"\n📊 Importing scale data for: {user_email}")
    print(f"📁 File: {csv_path}")

    confirm_execution(
        "Import Scale Data", {"user": user_email, "csv": csv_path, "dry_run": dry_run}
    )

    print("Parsing CSV...")
    try:
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            daily_data = parse_zepp_life_csv(content)
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
        print("✅ User validated\n")

    created = 0
    updated = 0

    print("=" * 80)
    print(
        f"{'Date':<12} {'Weight':>8} {'Fat %':>8} {'Muscle %':>8} {'BMR':>6} {'Status'}"
    )
    print("=" * 80)

    for date_str in sorted(daily_data.keys()):
        data = daily_data[date_str]

        try:
            log_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            log = WeightLog(
                user_email=user_email,
                date=log_date,
                source="scale_import_script",
                **data,  # type: ignore
            )

            status = "preview"
            if not dry_run and db:
                doc_id, is_new = db.save_weight_log(log)
                if is_new:
                    created += 1
                    status = "created ✓"
                else:
                    updated += 1
                    status = "updated ↻"

            fat_display = f"{log.body_fat_pct:.1f}%" if log.body_fat_pct else "-"
            muscle_display = (
                f"{log.muscle_mass_pct:.1f}%" if log.muscle_mass_pct else "-"
            )
            bmr_display = str(log.bmr) if log.bmr else "-"

            print(
                f"{date_str:<12} {log.weight_kg:>6.1f}kg {fat_display:>8} {muscle_display:>8} {bmr_display:>6} {status}"
            )

        except Exception as e:
            print(f"{date_str:<12} ERROR: {e}")

    print("=" * 80)
    print("\n📈 Summary:")
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
