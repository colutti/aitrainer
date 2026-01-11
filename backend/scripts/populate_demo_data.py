#!/usr/bin/env python3
import sys
import os
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.core.config import settings
    from scripts.utils import confirm_execution
except ImportError as e:
    print(f"Error importing settings: {e}")
    sys.exit(1)

def get_database():
    client = MongoClient(settings.MONGO_URI)
    return client[settings.DB_NAME]

def populate_demo_data(email="demo@demo.com"):
    db = get_database()
    print(f"Populating data for {email}...")

    # Clear existing logs for this user to avoid duplicates if re-run
    db.weight_logs.delete_many({"user_email": email})
    db.nutrition_logs.delete_many({"user_email": email})
    db.workout_logs.delete_many({"user_email": email})

    now = datetime.now(timezone.utc)
    
    # 0. User Profile Configuration (Ensure it's not 'maintain' if losing weight)
    db.users.update_one(
        {"email": email},
        {"$set": {
            "goal": "Perder peso de forma sustentável",
            "goal_type": "lose",
            "weekly_rate": 0.5
        }},
        upsert=True
    )
    print(f"✓ Configured user profile for {email}")
    
    # 1. Weight Logs (21 days, starting from 3 weeks ago)
    # 85kg -> 83kg (0.1kg/day roughly)
    start_weight = 85.0
    height_m = 1.78 # Avg height assumption
    
    for i in range(21):
        log_date = now - timedelta(days=(20 - i))
        
        # Add some noise to weight
        weight = start_weight - (i * 0.1) + (0.1 * (i % 3 - 1))
        
        # Composition Simulation
        # Fat goes down as weight goes down (25% -> ~24%)
        body_fat = 25.0 - (i * 0.08) + (0.2 * (i % 2 - 0.5))
        
        # Muscle goes up slightly (relative %)
        muscle_mass = 36.0 + (i * 0.04) + (0.1 * (i % 3 - 1))
        
        # Water fluctuates around 55%
        water = 55.0 + (0.5 * (i % 4 - 2))
        
        # Visceral fat (10 -> 9.5)
        visceral = 10.0 if i < 10 else 9.5
        
        # BMR (Rough estimation: 24 * weight)
        bmr = int(weight * 22)
        
        # BMI
        bmi = weight / (height_m * height_m)
        
        # Bone mass
        bone_mass = 3.1

        db.weight_logs.insert_one({
            "user_email": email,
            "date": log_date,
            "weight_kg": round(weight, 1),
            "body_fat_pct": round(body_fat, 2),
            "muscle_mass_pct": round(muscle_mass, 2),
            "body_water_pct": round(water, 2),
            "visceral_fat": visceral,
            "bone_mass_kg": bone_mass,
            "bmr": bmr,
            "bmi": round(bmi, 2),
            "source": "demo_script",
            "notes": "Daily check-in (Demo)"
        })
    print("✓ Added 21 weight logs")

    # 2. Nutrition Logs (21 days)
    # Avg 2200 kcal, High Protein
    for i in range(21):
        log_date = now - timedelta(days=(20 - i))
        # Simulate some variance
        calories = 2200 + (100 * (i % 2 - 0.5))
        protein = 180 + (5 * (i % 3 - 1))
        carbs = 200 + (20 * (i % 4 - 2))
        fat = 75 + (5 * (i % 5 - 2))
        
        db.nutrition_logs.insert_one({
            "user_email": email,
            "date": log_date,
            "calories": int(calories),
            "protein_grams": float(protein),
            "carbs_grams": float(carbs),
            "fat_grams": float(fat),
            "source": "chat",
            "notes": "Refeições equilibradas"
        })
    print("✓ Added 21 nutrition logs")

    # 3. Workout Logs (3 per week, PPL rotation)
    workouts = [
        {"type": "Push", "exercises": [
            {"name": "Supino Reto", "sets": 3, "reps_per_set": [10, 10, 8], "weights_per_set": [60, 60, 60]},
            {"name": "Desenvolvimento", "sets": 3, "reps_per_set": [12, 10, 10], "weights_per_set": [15, 15, 15]},
            {"name": "Tríceps Pulley", "sets": 3, "reps_per_set": [15, 12, 12], "weights_per_set": [25, 25, 25]}
        ]},
        {"type": "Pull", "exercises": [
            {"name": "Puxada Frontal", "sets": 3, "reps_per_set": [12, 10, 10], "weights_per_set": [50, 50, 50]},
            {"name": "Remada Curvada", "sets": 3, "reps_per_set": [10, 10, 8], "weights_per_set": [40, 40, 40]},
            {"name": "Rosca Direta", "sets": 3, "reps_per_set": [12, 10, 10], "weights_per_set": [10, 10, 10]}
        ]},
        {"type": "Legs", "exercises": [
            {"name": "Agachamento", "sets": 3, "reps_per_set": [12, 10, 10], "weights_per_set": [50, 50, 50]},
            {"name": "Leg Press", "sets": 3, "reps_per_set": [15, 12, 12], "weights_per_set": [120, 140, 140]},
            {"name": "Cadeira Extensora", "sets": 3, "reps_per_set": [15, 15, 15], "weights_per_set": [40, 40, 40]}
        ]}
    ]

    workout_count = 0
    for i in range(21):
        # M-W-F schedule roughly
        if i % 7 in [1, 3, 5]:
            log_date = now - timedelta(days=(20 - i))
            workout_template = workouts[workout_count % 3]
            db.workout_logs.insert_one({
                "user_email": email,
                "date": log_date,
                "workout_type": workout_template["type"],
                "exercises": workout_template["exercises"],
                "duration_minutes": 60
            })
            workout_count += 1
    print(f"✓ Added {workout_count} workout logs")

    print("\n✅ Demo data population complete!")

if __name__ == "__main__":
    confirm_execution("Populate Demo Data")
    populate_demo_data()
