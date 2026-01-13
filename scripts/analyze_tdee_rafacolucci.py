
import os
import sys
from pymongo import MongoClient
from datetime import datetime, timedelta, date, timezone
import numpy as np
from pprint import pprint

# --- Configuration ---
uri = os.environ.get("MONGO_URI")
db_name = os.environ.get("DB_NAME", "aitrainerdb")
target_email = "rafacolucci@gmail.com"
lookback_weeks = 3

if not uri:
    print("MONGO_URI is not set.")
    sys.exit(1)

client = MongoClient(uri)
db = client[db_name]

print(f"--- Analyzing Metabolism for {target_email} ---")

# 1. Fetch User Profile
profile = db.users.find_one({"email": target_email})
if not profile:
    print("❌ User profile not found.")
    sys.exit(1)

print("\n[User Profile]")
print(f"Goal: {profile.get('goal_type')} ({profile.get('goal')})")
print(f"Weekly Rate: {profile.get('weekly_rate', 0)} kg/week")
print(f"Stats: {profile.get('age')}y, {profile.get('height')}cm, {profile.get('weight')}kg, {profile.get('gender')}")
print(f"Activity: {profile.get('activity_level')}")

# 2. Fetch Weight Logs
end_date = datetime.now()
start_date = end_date - timedelta(weeks=lookback_weeks)
print(f"\n[Weight Logs] (Lookback: {lookback_weeks} weeks, {start_date.date()} to {end_date.date()})")

weight_query = {
    "user_email": target_email,
    "date": {"$gte": start_date, "$lte": end_date}
}
weight_logs = list(db.weight_logs.find(weight_query).sort("date", 1))

print(f"Found {len(weight_logs)} weight logs.")
if len(weight_logs) > 0:
    for w in weight_logs:
        print(f"  - {w['date'].date()}: {w['weight_kg']} kg")
else:
    print("  ❌ No weight logs found in period.")

# 3. Fetch Nutrition Logs
print(f"\n[Nutrition Logs] ({start_date.date()} to {end_date.date()})")
nutrition_query = {
    "user_email": target_email,
    "date": {"$gte": start_date, "$lte": end_date}
}
nutrition_logs = list(db.nutrition_logs.find(nutrition_query).sort("date", 1))

print(f"Found {len(nutrition_logs)} nutrition logs.")
total_calories = 0
if len(nutrition_logs) > 0:
    for n in nutrition_logs:
        total_calories += n.get('calories', 0)
        # print(f"  - {n['date'].date()}: {n['calories']} kcal") # Too verbose if many
    avg_calories = total_calories / len(nutrition_logs)
    print(f"  Average Calories (Logged days): {avg_calories:.0f} kcal")
else:
    print("  ❌ No nutrition logs found in period.")
    avg_calories = 0

# 4. Manual Calculation Replication
print("\n[Analysis]")

if len(weight_logs) < 2 or len(nutrition_logs) < 7:
    print("❌ INSUFFICIENT DATA for Adaptive TDEE (Need 2+ weight logs and 7+ nutrition logs).")
    
    # Fallback: Estimated TDEE (Mifflin-St Jeor)
    weight_kg = profile.get('weight', 70)
    height_cm = profile.get('height', 175)
    age = profile.get('age', 30)
    gender = profile.get('gender', 'Masculino')
    activity = profile.get('activity_level', 'moderate')
    
    # BMR
    if gender == 'Masculino':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age) - 161
        
    activity_multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderate": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    
    # Mapping fix (if profile uses different keys)
    # Mapping assumed based on common conventions
    mult = activity_multipliers.get(activity, 1.55) 
    
    est_tdee = bmr * mult
    print(f"⚠️ Using ESTIMATED TDEE (Formula) due to lack of data:")
    print(f"  BMR ({gender}): {bmr:.0f} kcal")
    print(f"  Activity ({activity}): x{mult}")
    print(f"  Estimated TDEE: {est_tdee:.0f} kcal")
    
else:
    # Perform Regression
    x = []
    y = []
    base_date = weight_logs[0]['date']
    for w in weight_logs:
        days = (w['date'] - base_date).days
        x.append(days)
        y.append(w['weight_kg'])
    
    slope, intercept = np.polyfit(x, y, 1)
    
    days_elapsed = (weight_logs[-1]['date'] - weight_logs[0]['date']).days
    daily_weight_change = slope # kg/day
    
    caloric_surplus = daily_weight_change * 7700
    
    calculated_tdee = avg_calories - caloric_surplus
    
    print(f"  Days Elapsed: {days_elapsed}")
    print(f"  Weight Trend Slope: {slope:.4f} kg/day ({(slope*7):.2f} kg/week)")
    print(f"  Implied Daily Surplus/Deficit: {caloric_surplus:+.0f} kcal")
    print(f"  Avg Intake: {avg_calories:.0f} kcal")
    print(f"  -> Calculated Adaptive TDEE: {calculated_tdee:.0f} kcal")
    
    # Energy Balance Status
    energy_balance = avg_calories - calculated_tdee
    status = "maintenance"
    if energy_balance < -150: status = "deficit"
    elif energy_balance > 150: status = "surplus"
    
    print(f"  Status: {status} ({energy_balance:+.0f} kcal/day)")
    
    if status == "deficit":
        print("  ✅ Conclusion: User is losing weight, so they are in a deficit vs their TDEE.")
    elif status == "surplus":
        print("  ✅ Conclusion: User is gaining weight, so they are in a surplus vs their TDEE.")
    else:
        print("  ✅ Conclusion: User's weight is stable.")

print("\n[Service Verification]")
try:
    # Fix imports for script execution context
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    backend_root = os.path.join(project_root, "backend") # <--- Added backend folder
    sys.path.append(backend_root)

    print(f"Added to path: {backend_root}") # Debug

    from src.services.database import MongoDatabase
    from src.services.adaptive_tdee import AdaptiveTDEEService
    
    # Mock Database wrapper for the script's pymongo client
    # actually MongoDatabase takes a client or uri?
    # It takes settings usually.
    # Let's instantiate it properly.
    
    class ScriptDBWrapper(MongoDatabase):
        def __init__(self, raw_db):
            self.db = raw_db
            
    # The actual MongoDatabase expects to connect itself. 
    # Let's try to initialize it similarly or hack it.
    # Actually, simpler: just instantiate the service and monkeypatch the db methods it uses.
    
    # 1. Init Service with a mock DB that delegates to our script's `db`
    # The service uses: 
    # get_weight_logs_by_date_range, get_nutrition_logs_by_date_range, get_user_profile
    
    class MockServiceDB:
        def __init__(self, real_db):
            self.db = real_db
            
        def get_user_profile(self, email):
            # We already fetched profile, return object
            from src.api.models.user_profile import UserProfile
            p_data = self.db.users.find_one({"email": email})
            if p_data: return UserProfile(**p_data)
            return None
            
        def get_weight_logs_by_date_range(self, email, start, end):
            from src.api.models.weight_log import WeightLog
            # Note: start/end are dates, query expects datetimes
            s_dt = datetime.combine(start, datetime.min.time())
            e_dt = datetime.combine(end, datetime.max.time())
            logs = list(self.db.weight_logs.find({"user_email": email, "date": {"$gte": s_dt, "$lte": e_dt}}))
            return [WeightLog(**l) for l in logs]
            
        def get_nutrition_logs_by_date_range(self, email, start, end):
            from src.api.models.nutrition_log import NutritionLog
            logs = list(self.db.nutrition_logs.find({"user_email": email, "date": {"$gte": start, "$lte": end}}))
            return [NutritionLog(**l) for l in logs]

    mock_db = MockServiceDB(db)
    service = AdaptiveTDEEService(mock_db)
    
    result = service.calculate_tdee(target_email, lookback_weeks=lookback_weeks)
    print("Shape of Service Result:")
    pprint(result)
    
    print("\n✅ Service Logic Verification Completed.")

except Exception as e:
    print(f"❌ Failed to run Service Verification: {e}")
    import traceback
    traceback.print_exc()

