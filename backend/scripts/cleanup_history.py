#!/usr/bin/env python3
"""
One-time cleanup script for all users.

Removes:
1. System messages (tool results) from message_store
2. Error responses from message_store
3. Resets long_term_summary to force regeneration
4. Resets last_compaction_timestamp to trigger full reprocessing

Safe to run multiple times - only affects relevant documents.
"""

import json
import sys
from pymongo import MongoClient

# MongoDB production credentials
# NOTE: These are loaded from environment or .env.prod in production
MONGO_URI = "mongodb+srv://aitrainerdb:a78082e9277d44c9947eefdfd24f5dec@home.gxgnsjx.mongodb.net/?appName=home"
DB_NAME = "aitrainerdb"

def cleanup_history(dry_run=True):
    """Clean polluted history for all users."""

    print(f"🧹 Cleanup History Script (dry_run={dry_run})")
    print("=" * 60)

    # Connect to MongoDB
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        print(f"✅ Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        return False

    try:
        # Phase 1: Delete system messages from message_store
        print("\n📋 Phase 1: Deleting system messages from message_store")
        system_count = 0
        error_count = 0

        for doc in db.message_store.find():
            try:
                history = json.loads(doc["History"])
                msg_type = history.get("type", "")
                content = history.get("data", {}).get("content", "")

                if msg_type == "system":
                    system_count += 1
                    if not dry_run:
                        db.message_store.delete_one({"_id": doc["_id"]})

                elif content.startswith("Error processing request:"):
                    error_count += 1
                    if not dry_run:
                        db.message_store.delete_one({"_id": doc["_id"]})
            except (json.JSONDecodeError, KeyError):
                continue

        print(f"  System messages to delete: {system_count}")
        print(f"  Error messages to delete: {error_count}")
        print(f"  Total to delete: {system_count + error_count}")

        # Phase 2: Reset long_term_summary for all users
        print("\n📋 Phase 2: Resetting long_term_summary for all users")
        users_with_summary = db.users.count_documents({"long_term_summary": {"$ne": None}})
        print(f"  Users with long_term_summary: {users_with_summary}")

        if not dry_run:
            result = db.users.update_many(
                {"long_term_summary": {"$ne": None}},
                {"$set": {"long_term_summary": None}}
            )
            print(f"  ✅ Updated {result.modified_count} users")

        # Phase 3: Reset last_compaction_timestamp for all users
        print("\n📋 Phase 3: Resetting last_compaction_timestamp for all users")
        users_with_timestamp = db.users.count_documents({"last_compaction_timestamp": {"$ne": None}})
        print(f"  Users with last_compaction_timestamp: {users_with_timestamp}")

        if not dry_run:
            result = db.users.update_many(
                {"last_compaction_timestamp": {"$ne": None}},
                {"$set": {"last_compaction_timestamp": None}}
            )
            print(f"  ✅ Updated {result.modified_count} users")

        # Summary
        print("\n" + "=" * 60)
        if dry_run:
            print("🔍 DRY RUN - No changes made")
            print(f"   Would delete: {system_count + error_count} messages")
            print(f"   Would reset long_term_summary for: {users_with_summary} users")
            print(f"   Would reset timestamps for: {users_with_timestamp} users")
            print("\n💡 Run with --no-dry-run to execute the cleanup")
        else:
            print("✅ Cleanup completed successfully!")
            print(f"   Deleted: {system_count + error_count} messages")
            print(f"   Reset long_term_summary for: {users_with_summary} users")
            print(f"   Reset timestamps for: {users_with_timestamp} users")

        return True

    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

    finally:
        client.close()

if __name__ == "__main__":
    dry_run = "--no-dry-run" not in sys.argv
    success = cleanup_history(dry_run=dry_run)
    sys.exit(0 if success else 1)
