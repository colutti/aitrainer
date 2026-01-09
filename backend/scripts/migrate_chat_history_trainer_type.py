"""
Migration script to add 'trainer_type' metadata to existing chat history messages.
Sets default value 'atlas' for all historical messages that lack this field.
"""
import asyncio
import json
import ast
from src.services.database import MongoDatabase
from src.core.logs import logger
from src.core.config import settings

def _update_message_dict(msg):
    """Helper to update a message dictionary with trainer_type."""
    target_dict = msg
    if 'data' in msg:
        target_dict = msg['data']
        
    if 'additional_kwargs' not in target_dict:
        target_dict['additional_kwargs'] = {}
    
    if 'trainer_type' not in target_dict['additional_kwargs']:
        target_dict['additional_kwargs']['trainer_type'] = 'atlas'
        return True
    return False

async def migrate_history():
    print("🚀 Starting chat history migration...")
    print(f"DEBUG: Using DB_NAME={settings.DB_NAME}")
    print(f"DEBUG: Using MONGO_URI={settings.MONGO_URI[:15]}...{settings.MONGO_URI.split('@')[-1] if '@' in settings.MONGO_URI else '???'}")
    
    try:
        db = MongoDatabase()
        collection = db.database["message_store"]
        
        initial_doc_count = collection.count_documents({})
        print(f"DEBUG: Found {initial_doc_count} documents in 'message_store'")
        
        # Iterating manually to handle potential structure variations (String vs List)
        cursor = collection.find({})
        count = 0 # This 'count' will track updated sessions
        total_msgs = 0
        
        for doc in cursor:
            session_id = doc.get("SessionId")
            history = doc.get("History", [])
            modified = False
            
            # Handle case where History is a STRING
            if isinstance(history, str):
                history_data = None
                parsing_method = None
                
                print(f"DEBUG: Processing session {session_id}, history length: {len(history)}")

                # Try JSON loads first
                try:
                    history_data = json.loads(history)
                    parsing_method = 'json'
                    print("DEBUG: JSON parsing successful")
                except Exception as e1:
                    # Try AST literal_eval (python dict string)
                    try:
                        history_data = ast.literal_eval(history)
                        parsing_method = 'ast'
                        print("DEBUG: AST parsing successful")
                    except Exception as e2:
                        print(f"⚠️ Failed to parse history string for session {session_id}")
                        print(f"JSON Error: {e1}")
                        print(f"AST Error: {e2}")
                        continue

                # Prepare list of messages to process
                if isinstance(history_data, dict):
                    msgs_to_process = [history_data]
                    print("DEBUG: History parsed as single Dict")
                elif isinstance(history_data, list):
                    msgs_to_process = history_data
                    print(f"DEBUG: History parsed as List of {len(history_data)} items")
                else:
                    print(f"⚠️ Unknown parsed history type for session {session_id}: {type(history_data)}")
                    continue
                    
                # Process messages
                internal_modified = False
                for i, msg in enumerate(msgs_to_process):
                    print(f"DEBUG: Processing message {i}")
                    if _update_message_dict(msg):
                        internal_modified = True
                        total_msgs += 1
                        print("DEBUG: Message updated!")
                    else:
                        print("DEBUG: Message NOT updated (maybe already has field?)")
                
                if internal_modified:
                    # Serialize back to string
                    # If it was parsed with AST (python dict), we might want to dump as JSON now for standardization,
                    # OR dump as repr/str to maintain format. Let's dump as JSON to fix it moving forward.
                    if isinstance(history_data, dict):
                        doc["History"] = json.dumps(history_data)
                    else:
                        doc["History"] = json.dumps(history_data)
                    modified = True
            
            # Handle standard List case
            elif isinstance(history, list):
                for msg in history:
                    if _update_message_dict(msg):
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
