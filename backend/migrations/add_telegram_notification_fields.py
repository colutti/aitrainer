#!/usr/bin/env python3
"""
Migration: Add Telegram notification configuration fields to existing users.

This script adds the following fields to all documents in the 'users' collection:
- telegram_notify_on_workout (default: True)
- telegram_notify_on_nutrition (default: False)
- telegram_notify_on_weight (default: False)

Usage:
    cd backend
    python migrations/add_telegram_notification_fields.py
"""

import os
import sys
from pathlib import Path
import pymongo

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings


def migrate():
    """Execute migration to add Telegram notification fields."""
    try:
        print("[Migration] Starting: Adding Telegram notification fields...")
        print(f"[Migration] Connecting to MongoDB: {settings.MONGO_URI}")
        print(f"[Migration] Database: {settings.DB_NAME}")
        print(f"[Migration] Target collection: users")

        # Connect directly to MongoDB to bypass repository overhead
        client = pymongo.MongoClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        users_collection = db["users"]

        # Update all users with new fields
        result = users_collection.update_many(
            {},
            {
                "$set": {
                    "telegram_notify_on_workout": True,
                    "telegram_notify_on_nutrition": False,
                    "telegram_notify_on_weight": False,
                }
            },
        )

        print(f"[Migration] ✅ Migration completed successfully")
        print(f"[Migration] Documents matched: {result.matched_count}")
        print(f"[Migration] Documents modified: {result.modified_count}")

        # Close connection
        client.close()
        return True

    except Exception as e:
        print(f"[Migration] ❌ Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
