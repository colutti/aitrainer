import sys
import os
import argparse

# Add parent directory of 'backend' -> 'backend/src' to path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.deps import get_mongo_database, get_mem0_client


def count_and_delete_mongo(db, collection_name, query, dry_run=False):
    collection = db.database[collection_name]

    # SAFETY CHECK: Ensure query contains the user's email email if the collection expects it
    if collection_name == "message_store":
        if "SessionId" not in query:
            print(
                f"❌ SAFETY ERROR: Query for {collection_name} does not contain SessionId!"
            )
            return 0
    elif collection_name == "token_blocklist":
        if "sub" not in query:
            print(f"❌ SAFETY ERROR: Query for {collection_name} does not contain sub!")
            return 0
    elif collection_name in ["users", "invites"]:
        if "email" not in query:
            print(
                f"❌ SAFETY ERROR: Query for {collection_name} does not contain email!"
            )
            return 0
    elif collection_name in [
        "user_profiles",
        "trainer_profiles",
        "workout_logs",
        "nutrition_logs",
        "weight_logs",
    ]:
        # These collections use 'user_email' or 'email' depending on the model.
        # Based on inspection:
        # users: email
        # user_profiles: email (ref UserProfile)
        # trainer_profiles: user_email
        # workout_logs: user_email
        # nutrition_logs: user_email
        # weight_logs: user_email

        # Verification logic
        has_email = "email" in query
        has_user_email = "user_email" in query

        if not (has_email or has_user_email):
            print(
                f"❌ SAFETY ERROR: Query for {collection_name} does not contain email identifier!"
            )
            return 0

    count = collection.count_documents(query)

    # Double check by finding one document and verifying the email field matches exactly if found
    if count > 0:
        sample = collection.find_one(query)
        if sample:
            # Extract the value used in query to compare
            query_val = list(query.values())[
                0
            ]  # Simplification assumes single field query

            # Find the actual field in the doc that corresponds to the query key
            doc_val = sample.get(list(query.keys())[0])

            if doc_val != query_val:
                print(
                    f"❌ MISMATCH ERROR: Document found in {collection_name} but value {doc_val} != {query_val}"
                )
                return 0

    if not dry_run and count > 0:
        result = collection.delete_many(query)
        print(f"✅ Deleted {result.deleted_count} documents from '{collection_name}'")
    else:
        print(f"ℹ️  Found {count} documents in '{collection_name}'")
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Completely delete a user and all their data."
    )
    parser.add_argument("email", type=str, help="The email of the user to delete")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    email = args.email.strip()
    if not email:
        print("Error: Email cannot be empty.")
        sys.exit(1)

    print(f"\n🔍 Searching for user data for: {email}\n")

    # Connect to MongoDB
    try:
        mongo = get_mongo_database()
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    # Connect to Mem0
    try:
        mem0 = get_mem0_client()
    except Exception as e:
        print(f"❌ Failed to connect to Mem0: {e}")
        sys.exit(1)

    # 1. Analyze Data (Dry Run)
    # Define collection mapping based on actual database schema inspection
    mongo_collections = [
        ("users", {"email": email}),
        ("user_profiles", {"email": email}),
        ("trainer_profiles", {"user_email": email}),
        ("workout_logs", {"user_email": email}),
        ("nutrition_logs", {"user_email": email}),
        ("weight_logs", {"user_email": email}),
        ("invites", {"email": email}),
        ("message_store", {"SessionId": email}),
        ("token_blocklist", {"sub": email}),
    ]

    total_mongo_docs = 0
    print("--- MongoDB Data ---")
    for col_name, query in mongo_collections:
        count = count_and_delete_mongo(mongo, col_name, query, dry_run=True)
        total_mongo_docs += count

    print("\n--- Mem0/Vector Data ---")
    memories = []
    try:
        # Fetch all memories to count
        memories = mem0.get_all(user_id=email)
        # Handle dict response (results vs direct list)
        if isinstance(memories, dict):
            memories = memories.get("results", []) or memories.get("memories", [])
            
        # Ensure memories is a list of dicts for Pyright
        if not isinstance(memories, list):
            memories = []
        
        memories = [m for m in memories if isinstance(m, dict)]

        print(f"ℹ️  Found {len(memories)} memories in Vector Store")
    except Exception as e:
        print(f"⚠️  Could not fetch memories: {e}")

    # 2. Confirmation
    if total_mongo_docs == 0 and len(memories) == 0:
        print(f"\n⚠️  No data found for user '{email}'!")
        print("Nothing to delete.")
        sys.exit(0)

    print(f"\n🚨 WARNING: You are about to DELETE ALL DATA for '{email}'")
    print(f"   - {total_mongo_docs} documents in MongoDB")
    print(f"   - {len(memories)} memories in Vector Database")
    print("   This action is IRREVERSIBLE.\n")

    if not args.force:
        confirm = input("Type 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("Aborted.")
            sys.exit(0)

    # 3. Execution
    print("\n🗑️  Executing deletion...\n")

    # MongoDB Deletion
    for col_name, query in mongo_collections:
        count_and_delete_mongo(mongo, col_name, query, dry_run=False)

    # Mem0 Deletion
    if len(memories) > 0:
        try:
            # According to Mem0 docs, delete_all(user_id=...) is supported in newer versions.
            # We'll try it first, then fall back to individual deletion.
            if hasattr(mem0, "delete_all"):
                mem0.delete_all(user_id=email)
                print(f"✅ Deleted ALL memories for user_id={email}")
            else:
                # Fallback: Delete one by one
                print(
                    "ℹ️  'delete_all' method not found, deleting individual memories..."
                )
                deleted_count = 0
                for mem in memories:
                    mem_id = None
                    if isinstance(mem, dict):
                        mem_id = mem.get("id")
                    elif hasattr(mem, "id"):
                        mem_id = getattr(mem, "id", None)
                    
                    if mem_id:
                        mem0.delete(mem_id)
                        deleted_count += 1
                print(f"✅ Deleted {deleted_count} memories individually")
        except Exception as e:
            print(f"❌ Error deleting memories: {e}")

    print(f"\n✨ User '{email}' has been completely obliterated from the system.")


if __name__ == "__main__":
    main()
