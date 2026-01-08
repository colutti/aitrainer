"""
Script para migrar dados de workout existentes para o novo schema.
Converte 'reps' e 'weight_kg' para 'reps_per_set' e 'weights_per_set'.
"""
import os
import sys
from pymongo import MongoClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import settings

def migrate_workouts():
    """Migra workouts do formato antigo para o novo."""
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    collection = db.workout_logs
    
    # Encontrar todos os workouts com o formato antigo
    old_format_workouts = collection.find({
        "exercises.reps": {"$exists": True}
    })
    
    updated_count = 0
    
    for workout in old_format_workouts:
        new_exercises = []
        
        for exercise in workout.get("exercises", []):
            # Converter para novo formato
            sets = exercise.get("sets", 1)
            reps = exercise.get("reps", 1)
            weight_kg = exercise.get("weight_kg")
            
            # Criar listas
            reps_per_set = [reps] * sets
            weights_per_set = [weight_kg] * sets if weight_kg is not None else []
            
            new_exercise = {
                "name": exercise.get("name", "Exercício"),
                "sets": sets,
                "reps_per_set": reps_per_set,
                "weights_per_set": weights_per_set
            }
            new_exercises.append(new_exercise)
        
        # Atualizar o documento
        collection.update_one(
            {"_id": workout["_id"]},
            {"$set": {"exercises": new_exercises}}
        )
        updated_count += 1
        print(f"✓ Migrado workout {workout['_id']}")
    
    print(f"\n✅ Migração concluída! {updated_count} workouts atualizados.")
    client.close()

if __name__ == "__main__":
    print("Iniciando migração de dados de workout...")
    migrate_workouts()
