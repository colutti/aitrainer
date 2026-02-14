#!/usr/bin/env python3
"""
Backfill script for Hevy cardio exercises (distance and duration fields).

This script re-fetches workout details from the Hevy API and updates MongoDB
with distance_meters_per_set and duration_seconds_per_set for cardio exercises.

Usage:
    python scripts/backfill_hevy_cardio.py --all --dry-run
    python scripts/backfill_hevy_cardio.py --email user@example.com
"""

import argparse
import sys
import os
import asyncio
import time
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.config import settings
    from src.services.hevy_service import HevyService
    from src.repositories.workout_repository import WorkoutRepository
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)


def get_database():
    """Connects to MongoDB using settings."""
    try:
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        client.admin.command("ping")
        return db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)


def find_hevy_users(db):
    """Find all users with Hevy integration enabled."""
    try:
        users = list(db.users.find({
            "hevy_enabled": True,
            "hevy_api_key": {"$ne": None}
        }))
        return users
    except Exception as e:
        print(f"Error querying users: {e}")
        return []


def find_hevy_workouts(db, user_id):
    """Find all workouts with Hevy source and external_id."""
    try:
        workouts = list(db.workout_logs.find({
            "user_email": {"$in": [u.get("email") for u in db.users.find({"_id": user_id})]},
            "source": "hevy",
            "external_id": {"$ne": None}
        }))
        return workouts
    except Exception as e:
        print(f"Error querying workouts: {e}")
        return []


async def backfill_user(db, hevy_service, user, dry_run=False, verbose=False):
    """Backfill workouts for a single user."""
    email = user.get("email")
    api_key = user.get("hevy_api_key")

    if not api_key:
        print(f"⚠️  Skipping {email} — no Hevy API key")
        return {"email": email, "processed": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Find workouts with external_id (from Hevy)
    try:
        workouts = list(db.workout_logs.find({
            "user_email": email,
            "source": "hevy",
            "external_id": {"$ne": None}
        }))
    except Exception as e:
        print(f"❌ Error querying workouts for {email}: {e}")
        return {"email": email, "processed": 0, "updated": 0, "skipped": 0, "errors": 1}

    stats = {"email": email, "processed": 0, "updated": 0, "skipped": 0, "errors": 0}

    if not workouts:
        print(f"ℹ️  {email} — no Hevy workouts found")
        return stats

    print(f"\n📊 Processing {email} ({len(workouts)} workouts)")

    for workout in workouts:
        stats["processed"] += 1
        workout_id = workout.get("_id")
        external_id = workout.get("external_id")

        if verbose:
            print(f"  ├─ {external_id}...", end=" ", flush=True)

        try:
            # Fetch latest workout data from Hevy
            hevy_workout = await hevy_service.fetch_workout_by_id(api_key, external_id)

            if not hevy_workout:
                if verbose:
                    print("❌ fetch failed")
                stats["errors"] += 1
                continue

            # Extract cardio fields from exercises
            has_updates = False
            exercises_update = []

            for exercise in hevy_workout.get("exercises", []):
                exercise_update = {}
                distance_list = []
                duration_list = []

                for s in exercise.get("sets", []):
                    dist = s.get("distance_meters")
                    dur = s.get("duration_seconds")

                    distance_list.append(float(dist) if dist is not None else 0.0)
                    duration_list.append(int(dur) if dur is not None else 0)

                # Only include if we found any non-zero cardio data
                if any(d > 0 for d in distance_list) or any(d > 0 for d in duration_list):
                    exercise_update["distance_meters_per_set"] = distance_list
                    exercise_update["duration_seconds_per_set"] = duration_list
                    has_updates = True
                else:
                    # Always set, even if empty (for consistency)
                    exercise_update["distance_meters_per_set"] = distance_list
                    exercise_update["duration_seconds_per_set"] = duration_list

                exercises_update.append(exercise_update)

            if has_updates:
                # Update MongoDB if not dry-run
                if not dry_run:
                    db.workout_logs.update_one(
                        {"_id": workout_id},
                        {"$set": {"exercises.$[].distance_meters_per_set": [], "exercises.$[].duration_seconds_per_set": []}}
                    )

                    # Update each exercise individually
                    for idx, exercise_update in enumerate(exercises_update):
                        db.workout_logs.update_one(
                            {"_id": workout_id},
                            {"$set": {f"exercises.{idx}.distance_meters_per_set": exercise_update.get("distance_meters_per_set", []),
                                      f"exercises.{idx}.duration_seconds_per_set": exercise_update.get("duration_seconds_per_set", [])}}
                        )

                if verbose:
                    print("✅ updated")
                stats["updated"] += 1
            else:
                if verbose:
                    print("⊙ no cardio")
                stats["skipped"] += 1

            # Rate limiting: be nice to Hevy API
            await asyncio.sleep(0.5)

        except Exception as e:
            if verbose:
                print(f"❌ {str(e)[:40]}")
            stats["errors"] += 1

    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="Backfill Hevy cardio data (distance, duration) in MongoDB"
    )
    parser.add_argument(
        "--email",
        type=str,
        help="Process single user by email"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all users with Hevy enabled"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating database"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress for each workout"
    )

    args = parser.parse_args()

    if not args.email and not args.all:
        parser.print_help()
        sys.exit(1)

    # Safety check
    confirm_execution(
        "BACKFILL: Hevy Cardio Data",
        {
            "mode": "DRY RUN" if args.dry_run else "LIVE UPDATE",
            "target": f"{args.email}" if args.email else "All Hevy users"
        }
    )

    # Connect to database
    db = get_database()

    # Initialize Hevy service
    workout_repo = WorkoutRepository(db)
    hevy_service = HevyService(workout_repository=workout_repo)

    # Get users to process
    if args.email:
        users = list(db.users.find({"email": args.email}))
        if not users:
            print(f"❌ User {args.email} not found")
            sys.exit(1)
    else:
        users = find_hevy_users(db)

    if not users:
        print("❌ No users with Hevy integration found")
        sys.exit(1)

    print(f"\n🚀 Starting backfill for {len(users)} user(s)")
    print(f"   Mode: {'DRY RUN' if args.dry_run else '⚡ LIVE'}")

    # Process each user
    all_stats = []
    for user in users:
        stats = await backfill_user(db, hevy_service, user, dry_run=args.dry_run, verbose=args.verbose)
        all_stats.append(stats)

    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY")
    print("=" * 60)

    total_processed = sum(s["processed"] for s in all_stats)
    total_updated = sum(s["updated"] for s in all_stats)
    total_skipped = sum(s["skipped"] for s in all_stats)
    total_errors = sum(s["errors"] for s in all_stats)

    for stats in all_stats:
        status = "✅" if stats["errors"] == 0 else "⚠️"
        print(f"{status} {stats['email']}: {stats['processed']} processed, {stats['updated']} updated, {stats['skipped']} skipped, {stats['errors']} errors")

    print("-" * 60)
    print(f"Total: {total_processed} processed, {total_updated} updated, {total_skipped} skipped, {total_errors} errors")

    if args.dry_run:
        print("\n✅ Dry run completed. No database changes made.")
    else:
        print("\n✅ Backfill completed!")

    if total_errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
