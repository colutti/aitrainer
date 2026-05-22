#!/usr/bin/env python3
"""
Reset user data tool — LOCAL DEVELOPMENT ONLY.

Connects to MongoDB and Qdrant, deletes all data for a given user email,
but preserves the user account (login/authentication).

Safety:
- Refuses to run if the target database host is not localhost/127.0.0.1/mongo/qdrant
- Refuses to run if no email is provided
- Requires explicit --confirm flag

Usage:
    python scripts/reset_user_data.py --email rafacolucci@gmail.com --confirm
"""

import argparse
import os
import sys
from urllib.parse import urlparse

SAFE_HOSTS = {"localhost", "127.0.0.1", "mongo", "qdrant", "0.0.0.0"}

MONGO_COLLECTIONS = [
    ("message_store", "SessionId"),
    ("trainer_profiles", "user_email"),
    ("workout_logs", "user_email"),
    ("nutrition_logs", "user_email"),
    ("weight_logs", "user_email"),
    ("events", "user_email"),
    ("prompt_logs", "user_email"),
    ("plans", "user_email"),
    ("plan_discovery_states", "user_email"),
    ("invites", "email"),
    ("telegram_links", "user_email"),
    ("telegram_codes", "user_email"),
]

QDRANT_COLLECTION = "aitrainerdb"
QDRANT_PAYLOAD_FIELD = "user_id"


def _safety_check(mongo_uri: str, qdrant_host: str):
    uri_host = urlparse(mongo_uri).hostname or ""
    if uri_host not in SAFE_HOSTS:
        print(f"SECURITY BLOCKED: MongoDB host '{uri_host}' is not a known local host.")
        print(f"Allowed hosts: {', '.join(sorted(SAFE_HOSTS))}")
        sys.exit(1)

    if qdrant_host not in SAFE_HOSTS:
        print(f"SECURITY BLOCKED: Qdrant host '{qdrant_host}' is not a known local host.")
        print(f"Allowed hosts: {', '.join(sorted(SAFE_HOSTS))}")
        sys.exit(1)

    print(f"✓ Safety check passed (mongo={uri_host}, qdrant={qdrant_host})")


def _reset_mongodb(mongo_uri: str, db_name: str, email: str) -> list[dict]:
    import pymongo

    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    db = client[db_name]

    results = []
    for coll_name, field in MONGO_COLLECTIONS:
        collection = db[coll_name]
        result = collection.delete_many({field: email})
        count = result.deleted_count
        results.append({"collection": coll_name, "field": field, "deleted": count})
        if count:
            print(f"  🗑️  {coll_name}: deleted {count} document(s) where {field} = {email}")
        else:
            print(f"  ✓  {coll_name}: nothing to delete")

    client.close()
    return results


def _reset_qdrant(qdrant_host: str, qdrant_port: int, email: str) -> int | None:
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Filter, FieldCondition, MatchValue

        client = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=5)
        collections = client.get_collections().collections
        coll_names = [c.name for c in collections]

        if QDRANT_COLLECTION not in coll_names:
            print(f"  ✓  qdrant '{QDRANT_COLLECTION}': collection not found, skipping")
            return 0

        count_result = client.count(
            collection_name=QDRANT_COLLECTION,
            count_filter=Filter(
                must=[
                    FieldCondition(
                        key=QDRANT_PAYLOAD_FIELD,
                        match=MatchValue(value=email),
                    )
                ]
            ),
        )
        total = count_result.count

        if total == 0:
            print(f"  ✓  qdrant '{QDRANT_COLLECTION}': nothing to delete for {email}")
            return 0

        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key=QDRANT_PAYLOAD_FIELD,
                        match=MatchValue(value=email),
                    )
                ]
            ),
        )
        print(f"  🗑️  qdrant '{QDRANT_COLLECTION}': deleted {total} point(s) for {email}")
        return total
    except Exception as exc:
        print(f"  ⚠️  qdrant: {exc}")
        return None


def _reset_user_counters(mongo_uri: str, db_name: str, email: str):
    import pymongo
    client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]
    result = db["users"].update_one(
        {"email": email},
        {"$set": {
            "messages_sent_today": 0,
            "messages_sent_this_month": 0,
            "daily_messages_sent": 0,
            "last_message_date": None,
            "subscription_plan": "Basic",
        }}
    )
    if result.modified_count:
        print("  🗑️  users: reset message counters (daily=0, monthly=0) and upgraded to Basic")
    elif result.matched_count:
        print("  ✓  users: counters already zero or plan already Basic")
    else:
        print(f"  ⚠️  users: user {email} not found")
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Reset user data (LOCAL ONLY). Preserves login account."
    )
    parser.add_argument(
        "--email",
        required=True,
        help="User email to reset",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Must be set to actually execute. Without it, runs in dry-run mode.",
    )
    args = parser.parse_args()

    email = args.email.strip().lower()

    mongo_uri = os.environ.get(
        "MONGO_URI", "mongodb://aitrainer:aitrainerpass@localhost:27017/aitrainerdb?authSource=admin"
    )
    db_name = os.environ.get("DB_NAME", "aitrainerdb")
    qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
    qdrant_port = int(os.environ.get("QDRANT_PORT", "6333"))

    print("=" * 60)
    print("  FITYQ — RESET USER DATA (LOCAL ONLY)")
    print("=" * 60)
    print()
    print(f"  User:       {email}")
    print(f"  Mode:       {'EXECUTE' if args.confirm else 'DRY-RUN (--confirm needed)'}")
    print(f"  Mongo URI:  {mongo_uri}")
    print(f"  Mongo DB:   {db_name}")
    print(f"  Qdrant:     {qdrant_host}:{qdrant_port}/{QDRANT_COLLECTION}")
    print()

    _safety_check(mongo_uri, qdrant_host)

    print()
    print("  Data to DELETE (keeps users/account):")
    print("  -) users collection: KEPT (login preserved)")
    print("  -) users counters: RESET (messages_sent=0, plan=Basic)")
    print("  -) token_blocklist: KEPT (not user-specific)")
    for coll, field in MONGO_COLLECTIONS:
        print(f"  -) {coll}: DELETE where {field} = {email}")
    print(f"  -) qdrant.{QDRANT_COLLECTION}: DELETE where {QDRANT_PAYLOAD_FIELD} = {email}")
    print()

    if not args.confirm:
        print("  ❯ Dry-run complete. Pass --confirm to execute.")
        sys.exit(0)

    print("  Executing...")
    print()

    print("  [MongoDB]")
    mongo_results = _reset_mongodb(mongo_uri, db_name, email)

    print()
    print("  [Qdrant]")
    qdrant_result = _reset_qdrant(qdrant_host, qdrant_port, email)

    print()
    print("  [User counters]")
    _reset_user_counters(mongo_uri, db_name, email)

    print()
    total_deleted = sum(r["deleted"] for r in mongo_results)
    print(f"  Done! MongoDB: {total_deleted} documents deleted.")
    if qdrant_result is not None:
        print(f"        Qdrant:  {qdrant_result} points deleted.")
    else:
        print("        Qdrant:  skipped (error)")

    print()
    print("  ✓ User data reset complete. Login preserved.")


if __name__ == "__main__":
    main()
