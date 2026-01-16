import os
import sys
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cleanup_user_duplicates(user_email: str, mongo_uri: str, db_name: str, tz_offset: int = -3):
    """
    Finds and removes duplicate workout logs for a user using an aggressive day-level strategy.
    Prioritizes workouts with an 'external_id'.
    `tz_offset` is used to group by local calendar day (default -3 for Brazil).
    """
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['workout_logs']

    logger.info(f"Scanning for aggressive duplicates for {user_email} (TZ offset: {tz_offset})")
    
    # Get all workouts for user sorted by date desc
    workouts = list(collection.find({"user_email": user_email}).sort("date", -1))
    logger.info(f"Found {len(workouts)} total workouts for user.")

    # Group by day adjusted for timezone
    days = {}
    for w in workouts:
        # Adjust date for local timezone to group by calendar day accurately
        local_date = w['date'] + timedelta(hours=tz_offset)
        d = local_date.date()
        if d not in days:
            days[d] = []
        days[d].append(w)

    to_delete = []
    
    for day, day_workouts in days.items():
        if len(day_workouts) <= 1:
            continue
            
        logger.info(f"Day {day} has {len(day_workouts)} workouts. Deduplicating...")
        
        # Sort workouts: primary = has external_id, secondary = newest date
        # We want to KEEP the best one
        day_workouts.sort(key=lambda x: (1 if x.get('external_id') else 0, x['date']), reverse=True)
        
        keep_this_one = day_workouts[0]
        others = day_workouts[1:]
        
        for w in others:
            logger.info(f"Marking for deletion: ID={w['_id']}, Date={w['date']}, Type={w.get('workout_type')}, Source={w.get('source')}, ExtID={w.get('external_id')}")
            to_delete.append(w['_id'])
            
        logger.info(f"Keeping: ID={keep_this_one['_id']}, Date={keep_this_one['date']}, Type={keep_this_one.get('workout_type')}, ExtID={keep_this_one.get('external_id')}")

    if to_delete:
        logger.info(f"Deleting {len(to_delete)} duplicates...")
        result = collection.delete_many({"_id": {"$in": to_delete}})
        logger.info(f"Successfully deleted {result.deleted_count} duplicates.")
    else:
        logger.info("No duplicates found.")

    client.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cleanup_duplicates.py <user_email> [tz_offset]")
        sys.exit(1)

    user_email = sys.argv[1]
    tz_offset = int(sys.argv[2]) if len(sys.argv) > 2 else -3
    
    # Use environment variable or default local
    mongo_uri = os.getenv("MONGO_URI", "mongodb://aitrainer:aitrainerpass@localhost:27017/aitrainerdb?authSource=admin")
    db_name = "aitrainerdb"

    cleanup_user_duplicates(user_email, mongo_uri, db_name, tz_offset)
