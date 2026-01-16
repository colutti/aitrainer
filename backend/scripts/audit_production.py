import os
from datetime import datetime, timedelta
import logging
from pymongo import MongoClient
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def audit_production(user_email: str, mongo_uri: str, db_name: str):
    client = MongoClient(mongo_uri)
    db = client[db_name]
    collection = db['workout_logs']

    logger.info(f"Auditing workouts for {user_email} in production")
    
    # Get Jan 2026 workouts
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 1, 31)
    
    workouts = list(collection.find({
        "user_email": user_email,
        "date": {"$gte": start_date, "$lt": end_date}
    }).sort("date", 1))

    print(f"\nAudit results for {user_email} (Jan 2026):\n")
    print(f"{'ID':<25} | {'Date (UTC)':<25} | {'Type':<20} | {'ExtID':<20} | {'Source':<10}")
    print("-" * 110)
    
    for w in workouts:
        print(f"{str(w['_id']):<25} | {str(w['date']):<25} | {str(w.get('workout_type')):<20} | {str(w.get('external_id')):<20} | {str(w.get('source')):<10}")

    client.close()

if __name__ == "__main__":
    user_email = "rafacolucci@gmail.com"
    mongo_uri = "mongodb+srv://aitrainerdb:a78082e9277d44c9947eefdfd24f5dec@home.gxgnsjx.mongodb.net/?appName=home"
    db_name = "aitrainerdb"

    audit_production(user_email, mongo_uri, db_name)
