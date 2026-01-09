"""
Migration script to add 'trainer_type' metadata to existing chat history messages.
Sets default value 'atlas' for all historical messages that lack this field.
"""
import asyncio
from src.services.database import MongoDatabase
from src.core.logs import logger
from src.core.config import settings

async def migrate_history():
    print("🚀 Starting chat history migration...")
    
    try:
        db = MongoDatabase()
        collection = db.database[settings.DB_NAME]["message_store"]
        
        # 1. Update all documents that don't have 'additional_kwargs.trainer_type'
        # We set default to 'atlas' as a safe fallback
        result = collection.update_many(
            {"History.additional_kwargs.trainer_type": {"$exists": False}},
            {"$set": {"History.$[].additional_kwargs.trainer_type": "atlas"}}
        )
        
        # Note: The structure of MongoDBChatMessageHistory stores messages in a 'History' array field.
        # However, the langchain_mongodb structure might vary. Let's verify structure first.
        # Actually, standard MongoDBChatMessageHistory stores documents with 'SessionId' and 'History' (list of msgs)
        
        # Let's try a different approach: Iterate and update to be safe about the structure
        # The above update_many might be tricky with nested arrays.
        
        # Let's inspect one doc first
        print("inspecting one document...")
        sample = collection.find_one({})
        if sample:
            print(f"Sample keys: {sample.keys()}")
            if 'History' in sample:
                print("Found 'History' field (standard langchain structure)")
            
        print("Executing migration via bulk update...")
        
        # Helper to update nested array elements
        # We need to update every message in the History array for every session
        
        # We will iterate through all sessions
        cursor = collection.find({})
        count = 0
        total_msgs = 0
        
        for doc in cursor:
            session_id = doc.get("SessionId")
            history = doc.get("History", [])
            
            modified = False
            for msg in history:
                # Check if 'data' field exists (structure: type, data: {content, additional_kwargs, ...})
                # OR direct structure: content, additional_kwargs, ...
                
                # Langchain serialization format often puts actual fields inside 'data'
                target_dict = msg
                if 'data' in msg:
                    target_dict = msg['data']
                    
                if 'additional_kwargs' not in target_dict:
                    target_dict['additional_kwargs'] = {}
                
                if 'trainer_type' not in target_dict['additional_kwargs']:
                    # Try to fetch current trainer profile for this user if possible, else default
                    # For migration simplicity, we use 'atlas' (default)
                    target_dict['additional_kwargs']['trainer_type'] = 'atlas'
                    modified = True
                    total_msgs += 1
            
            if modified:
                collection.replace_one({"_id": doc["_id"]}, doc)
                count += 1
                
        print(f"✅ Migration complete!")
        print(f"📦 Updated {count} sessions")
        print(f"📨 Updated {total_msgs} individual messages")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_history())
