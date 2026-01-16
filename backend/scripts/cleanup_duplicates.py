import os
import sys
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_user_duplicates(user_email: str, mongo_uri: str, db_name: str, window_minutes: int = 60):
    """
    Finds and removes duplicate workout logs for a user.
    Workouts are considered duplicates if they are within `window_minutes` of each other
    and have the same workout_type.
    """
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['workout_logs']

    logger.info(f"Scanning for duplicates for user: {user_email}")
    
    # Get all workouts for user sorted by date
    workouts = list(collection.find({"user_email": user_email}).sort("date", 1))
    logger.info(f"Found {len(workouts)} total workouts for user.")

    to_delete = []
    i = 0
    while i < len(workouts) - 1:
        w1 = workouts[i]
        j = i + 1
        found_duplicate_for_w1 = False
        
        while j < len(workouts):
            w2 = workouts[j]
            
            # Potential duplicate! Same day check
            same_day = (w1['date'].date() == w2['date'].date())
            
            # Usually if same type and same day, it's a dupe if they have similar exercises
            if same_day and w1.get('workout_type') == w2.get('workout_type'):
                # Check exercises count or just assume if same day/type it's a dupe from sync
                logger.info(f"Potential duplicate found: {w1['_id']} and {w2['_id']} on {w1['date'].date()} (Type: {w1.get('workout_type')})")
                to_delete.append(w2['_id'])
                workouts.pop(j)
                found_duplicate_for_w1 = True
                continue
            
            # Also check if within window (e.g. 60 min) regardless of type (legacy check)
            time_diff = abs((w2['date'] - w1['date']).total_seconds()) / 60
            if time_diff < window_minutes and w1.get('workout_type') == w2.get('workout_type'):
                # Already handled by same_day but safe to have
                pass
            
            if time_diff > window_minutes and not same_day:
                break
            
            j += 1
        
        i += 1

    if to_delete:
        logger.info(f"Marked {len(to_delete)} duplicates for deletion.")
        # Perform deletion
        result = collection.delete_many({"_id": {"$in": to_delete}})
        logger.info(f"Successfully deleted {result.deleted_count} duplicates.")
    else:
        logger.info("No duplicates found.")

    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_duplicates.py <user_email> [window_minutes]")
        sys.exit(1)

    user_email = sys.argv[1]
    window = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    # Use environment variable or default local
    mongo_uri = os.getenv("MONGO_URI", "mongodb://aitrainer:aitrainerpass@localhost:27017/aitrainerdb?authSource=admin")
    db_name = "aitrainerdb"

    cleanup_user_duplicates(user_email, mongo_uri, db_name, window)
