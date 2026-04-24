#!/usr/bin/env python3
import argparse
import sys
import os
from typing import Optional
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Add backend directory to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.config import settings
    from src.api.models.user_profile import UserProfile
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing app modules: {e}")
    print("Make sure you are running this script from the 'backend' directory.")
    sys.exit(1)


def get_mongo_client(uri: str) -> MongoClient:
    try:
        # Strip quotes if present
        uri = uri.strip("'").strip('"')
        client = MongoClient(uri)
        # Force connection check
        client.admin.command("ping")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Mongo URI: {uri} \nError: {e}")
        sys.exit(1)


def get_qdrant_client_from_args(url: str, api_key: Optional[str]) -> QdrantClient | None:
    try:
        if not url:
            return None
        
        # Strip quotes
        url = url.strip("'").strip('"')
        if api_key:
            api_key = api_key.strip("'").strip('"')

        # If url doesn't have port and it's not http/s, assume it's host
        if "://" not in url and ":" not in url:
             # Just hostname? logic similar to deps.py
             pass 

        client = QdrantClient(url=url, api_key=api_key)
        # Check connection
        client.get_collections()
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Qdrant URL: {url} \nError: {e}")
        sys.exit(1)


def sync_mongo_collection(
    src_db, dest_db, collection_name: str, user_email: str, id_field: str = "user_email"
):
    """
    Syncs a single MongoDB collection for a specific user.
    """
    if collection_name not in src_db.list_collection_names():
        print(f"⚠️  Collection '{collection_name}' not found in Source. Skipping.")
        return

    src_coll = src_db[collection_name]
    dest_coll = dest_db[collection_name]

    # Special handling for LangChain's 'chat_history' or 'message_store'
    # which usually keys by 'SessionId' instead of 'user_email'
    query = {}
    if collection_name in ["chat_history", "message_store"]:
        # LangChain MongoDBChatMessageHistory uses 'SessionId'
        query = {"SessionId": user_email}
    else:
        query = {id_field: user_email}

    # 1. Fetch from Source
    docs = list(src_coll.find(query))
    count = len(docs)
    
    if count == 0:
        print(f"ℹ️  Collection '{collection_name}': No documents found for user.")
        return

    # 2. Delete from Destination
    delete_result = dest_coll.delete_many(query)
    
    # 3. Process and Insert into Destination
    processed_docs = []
    for doc in docs:
        if collection_name == "users":
            try:
                # Ensure it matches local UserProfile schema (fills defaults)
                # We exclude computed fields to avoid stale data in DB
                profile = UserProfile(**doc)
                
                # If it's an admin, we might want to default to Premium plan 
                # (adjust this based on actual project preference if known)
                if profile.role == "admin" and not doc.get("subscription_plan"):
                    profile.subscription_plan = "Premium"
                
                # model_dump() with computed_fields=False (default is False in V2, 
                # but let's be explicit if needed, though Pydantic V2 doesn't 
                # usually include them unless told to). 
                # In this project's version, they seem to be included.
                # Actually, let's use exclude manually if they are appearing.
                data = profile.model_dump()
                # Remove common computed fields just in case
                for cf in ["trial_remaining_days", "current_daily_limit", "effective_remaining_messages"]:
                    data.pop(cf, None)
                
                processed_docs.append(data)
            except Exception as e:
                print(f"⚠️  Schema mismatch for user {user_email}: {e}. Inserting raw document.")
                processed_docs.append(doc)
        else:
            processed_docs.append(doc)

    if processed_docs:
        dest_coll.insert_many(processed_docs)

    print(f"✅ Collection '{collection_name}': Synced {count} documents (Deleted {delete_result.deleted_count} local).")


def sync_qdrant(
    src_client: QdrantClient, 
    dest_client: QdrantClient, 
    user_email: str, 
    src_collection: str,
    dest_collection: str
):
    """
    Syncs Qdrant points for a user.
    """
    if not src_client:
        print("⚠️  No Source Qdrant configured. Skipping Vector Sync.")
        return

    print(f"\n🔄 Syncing Qdrant: {src_collection} -> {dest_collection}...")

    # 1. Delete existing points for user in Destination
    # Filter: payload.user_id == user_email
    user_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_email)
            )
        ]
    )
    
    try:
        dest_client.delete(
            collection_name=dest_collection,
            points_selector=models.FilterSelector(filter=user_filter)
        )
        print("   Deleted existing local points.")
    except Exception as e:
         print(f"   ⚠️  Could not delete existing points (Collection might not exist yet): {e}")

    # 2. Scroll (Fetch) all points from Source
    points = []
    next_offset = None
    
    # Check if source collection exists
    try:
        src_client.get_collection(src_collection)
    except Exception:
        print(f"❌ Source Qdrant collection '{src_collection}' does not exist.")
        return

    # Ensure dest collection exists (create if needed - basic copy)
    try:
        dest_client.get_collection(dest_collection)
    except Exception:
        print(f"   Destination collection '{dest_collection}' missing. Creating...")
        dest_client.create_collection(
            collection_name=dest_collection,
            vectors_config=models.VectorParams(
                size=settings.OPENROUTER_EMBED_DIMENSIONS,
                distance=models.Distance.COSINE,
            ),
        )

    print("   Fetching points from Source...")
    while True:
        batch, next_offset = src_client.scroll(
            collection_name=src_collection,
            scroll_filter=user_filter,
            limit=100,
            offset=next_offset,
            with_payload=True,
            with_vectors=True
        )
        points.extend(batch)
        if next_offset is None:
            break
            
    if not points:
        print("   No vector points found for this user in Source.")
        return

    print(f"   Fetched {len(points)} points. Uploading to Destination...")
    
    # Convert Record objects to PointStruct
    upsert_points = []
    for p in points:
        upsert_points.append(
            models.PointStruct(
                id=p.id,
                vector=p.vector,
                payload=p.payload
            )
        )
    
    # 3. Upsert to Destination
    dest_client.upsert(
        collection_name=dest_collection,
        points=upsert_points
    )
    print(f"✅ Qdrant Sync Complete: {len(points)} points transferred.")


def validate_local_import(dest_db, user_email: str) -> None:
    """Validates that the local import contains the expected user data."""
    expected_queries = {
        "users": {"email": user_email},
        "trainer_profiles": {"user_email": user_email},
        "workout_logs": {"user_email": user_email},
        "nutrition_logs": {"user_email": user_email},
        "weight_logs": {"user_email": user_email},
        "prompt_logs": {"user_email": user_email},
        "message_store": {"SessionId": user_email},
    }
    minimum_counts = {
        "users": 1,
        "trainer_profiles": 1,
        "workout_logs": 1,
        "nutrition_logs": 1,
        "weight_logs": 1,
        "prompt_logs": 1,
        "message_store": 1,
    }

    print("\n✅ Running post-import validation...")
    for collection_name, query in expected_queries.items():
        count = dest_db[collection_name].count_documents(query)
        print(f"   Validation {collection_name}: {count} document(s)")
        if count < minimum_counts[collection_name]:
            raise RuntimeError(
                f"Validation failed for {collection_name}: "
                f"expected at least {minimum_counts[collection_name]}, got {count}"
            )

    print("✅ Post-import validation passed.")


def main():
    parser = argparse.ArgumentParser(description="Sync User Data from PROD to LOCAL")
    parser.add_argument("--email", required=True, help="User email to sync")
    parser.add_argument("--source-uri", required=True, help="Source MongoDB URI (PROD)")
    parser.add_argument("--source-db", default="aitrainerdb", help="Source Database name (PROD, default: aitrainerdb)")
    parser.add_argument("--prod-qdrant-url", help="Source Qdrant URL (PROD)")
    parser.add_argument("--prod-qdrant-key", help="Source Qdrant API Key (PROD)")
    parser.add_argument("--src-collection", help="Source Qdrant collection name")
    parser.add_argument("--dest-collection", help="Destination Qdrant collection name (local)")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation")

    args = parser.parse_args()

    local_uri = settings.MONGO_URI
    local_db_name = settings.DB_NAME
    src_db_name = args.source_db
    src_collection = args.src_collection or settings.QDRANT_COLLECTION_NAME
    dest_collection = args.dest_collection or settings.QDRANT_COLLECTION_NAME
    
    # Safety Check (Removed as per user request)
    print(f"🚀 Syncing {args.email} from PROD to LOCAL...")

    # --- MongoDB Sync ---
    print("\n🐘 Connecting to MongoDBs...")
    src_mongo = get_mongo_client(args.source_uri)
    dest_mongo = get_mongo_client(local_uri)

    src_db = src_mongo[src_db_name]
    dest_db = dest_mongo[local_db_name]
    
    # Verify User in Source
    user = src_db.users.find_one({"email": args.email})
    if not user:
        print(f"❌ User '{args.email}' not found in Source Database!")
        sys.exit(1)
        
    print(f"✅ User found in Source: {user.get('_id')}")
    
    # Map collections to their ID field
    collections_map = {
        "users": "email",
        "trainer_profiles": "user_email",
        "workout_logs": "user_email",
        "nutrition_logs": "user_email",
        "weight_logs": "user_email",
        "prompt_logs": "user_email",
        "chat_history": "SessionId", 
        "message_store": "SessionId"
    }
    
    print("\n🔄 Syncing MongoDB Collections...")
    for coll_name, id_field in collections_map.items():
        sync_mongo_collection(src_db, dest_db, coll_name, args.email, id_field)
        
    # --- Qdrant Sync ---
    if args.prod_qdrant_url:
        print("\n🔮 Connecting to Qdrant...")
        
        # Source Qdrant
        src_qdrant = get_qdrant_client_from_args(args.prod_qdrant_url, args.prod_qdrant_key)
        
        # Local Qdrant
        if settings.QDRANT_HOST.startswith("http"):
            qdrant_url = settings.QDRANT_HOST
            if str(settings.QDRANT_PORT) not in qdrant_url:
                qdrant_url = f"{qdrant_url}:{settings.QDRANT_PORT}"
            dest_qdrant = QdrantClient(url=qdrant_url, api_key=settings.QDRANT_API_KEY)
        else:
            dest_qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        
        if src_qdrant:
            sync_qdrant(
                src_qdrant, 
                dest_qdrant, 
                args.email, 
                src_collection,
                dest_collection
            )
        else:
            print("⚠️ Skipping Qdrant sync: Could not initialize source client.")
    else:
        print("\n⏭️  Skipping Qdrant Sync (No PROD URL provided).")

    validate_local_import(dest_db, args.email)

    print("\n✨ Sync Completed Successfully! ✨\n")


if __name__ == "__main__":
    main()
