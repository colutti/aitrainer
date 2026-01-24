#!/usr/bin/env python3
import sys
import os
from pymongo import MongoClient

# Add backend directory to sys.path to allow imports from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from src.core.config import settings
    from src.services.adaptive_tdee import AdaptiveTDEEService
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

def migrate():
    confirm_execution("Migrate Trend Weights (EMA)", {"description": "Calculates and updates trend_weight for all historical weight logs using the new EMA algorithm."})
    
    try:
        client = MongoClient(settings.MONGO_URI)
        db = client[settings.DB_NAME]
        # Pymongo lazy connection, force a check
        client.admin.command("ping")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

    tdee_service = AdaptiveTDEEService(None)  # db=None is fine for calculate_ema_trend

    users = db.users.find({}, {"email": 1})
    total_users = 0
    total_logs = 0

    for user in users:
        email = user["email"]
        print(f"Processing user: {email}...", end="", flush=True)
        
        # Get all logs for this user sorted by date ASC
        logs = list(db.weight_logs.find({"user_email": email}).sort("date", 1))
        
        prev_trend = None
        user_logs_count = 0
        for log in logs:
            weight = log.get("weight_kg")
            if weight is None:
                continue
                
            # Calculate EMA Trend
            new_trend = tdee_service.calculate_ema_trend(weight, prev_trend)
            
            # Update the document
            db.weight_logs.update_one(
                {"_id": log["_id"]},
                {"$set": {"trend_weight": new_trend}}
            )
            
            prev_trend = new_trend
            user_logs_count += 1
            total_logs += 1
        
        print(f" Done ({user_logs_count} logs).")
        total_users += 1

    print(f"\nMigration complete!")
    print(f"Processed {total_users} users and {total_logs} weight logs.")

if __name__ == "__main__":
    migrate()
