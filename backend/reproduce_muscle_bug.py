import requests
import jwt
import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

# Configuration
SECRET_KEY = "A4C6B3DB-1B13-4B5A-A057-C59F13E1C771" # From .env local
MONGO_URI = "mongodb://aitrainer:aitrainerpass@localhost:27017/aitrainerdb?authSource=admin"
DB_NAME = "aitrainerdb"
URL = "http://localhost:8000/weight"
EMAIL = "rafacolucci@gmail.com"

def reproduce_bug():
    # 1. Create Token
    payload = {'sub': EMAIL, 'exp': datetime.now(timezone.utc) + timedelta(hours=1)}
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    headers = {'Authorization': f'Bearer {token}'}

    # 2. Prepare Payload with Muscle Mass
    test_date = "2026-01-13"
    test_payload = {
        "date": test_date,
        "weight_kg": 77.5,
        "muscle_mass_pct": 55.5,  # The value user says is missing
        "body_fat_pct": 24.0,
        "source": "manual"
    }

    print(f"Sending payload: {test_payload}")
    response = requests.post(URL, json=test_payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")

    if response.status_code != 200:
        print("Failed to save entry.")
        return

    # 3. Verify in Database
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    log = db.weight_logs.find_one({"user_email": EMAIL, "date": datetime(2026, 1, 13)})

    if log:
        print("\nRecord found in DB:")
        print(f"  User: {log.get('user_email')}")
        print(f"  Date: {log.get('date')}")
        print(f"  Weight: {log.get('weight_kg')} kg")
        print(f"  Muscle Mass: {log.get('muscle_mass_pct')} %")
        print(f"  Body Fat: {log.get('body_fat_pct')} %")
        
        if log.get('muscle_mass_pct') == 55.5:
            print("\nSUCCESS: Muscle Mass was saved correctly.")
        else:
            print("\nBUG PROVEN: Muscle Mass value is MISSING or INCORRECT in DB.")
    else:
        print("\nERROR: Record NOT found in database.")

if __name__ == "__main__":
    reproduce_bug()
