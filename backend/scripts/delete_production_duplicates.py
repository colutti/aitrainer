import os
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delete_production_duplicates(user_email: str, mongo_uri: str, db_name: str):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['workout_logs']

    logger.info(f"Targeted deletion for {user_email} in production")
    
    # Specific IDs identified in audit (Jan 12, 13, 14 non-Hevy ones)
    to_delete = [
        ObjectId("6967aed192f4e7d682372282"), # Jan 12 Push (Manual)
        ObjectId("6967afffe30964dbed850096"), # Jan 13 Pernas (Manual)
        ObjectId("69696188a94ff77db7b4049b"), # Jan 14 Costas (Pull) (Manual/Midnight)
    ]
    
    logger.info(f"Marking {len(to_delete)} specific IDs for deletion")
    
    result = collection.delete_many({"_id": {"$in": to_delete}})
    logger.info(f"Successfully deleted {result.deleted_count} duplicates.")

    client.close()

if __name__ == "__main__":
    user_email = "rafacolucci@gmail.com"
    mongo_uri = "mongodb+srv://aitrainerdb:a78082e9277d44c9947eefdfd24f5dec@home.gxgnsjx.mongodb.net/?appName=home"
    db_name = "aitrainerdb"

    delete_production_duplicates(user_email, mongo_uri, db_name)
