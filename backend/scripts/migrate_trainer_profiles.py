"""
Script para migrar perfis de treinadores existentes para garantir integridade.
Verifica campos obrigatórios (gender, style) e aplica defaults se necessário.
"""
import os
import sys
from pymongo import MongoClient

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.config import settings

def migrate_trainer_profiles():
    """Valida e corrige perfis de treinador."""
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DB_NAME]
    collection = db.trainer_profiles
    
    # Encontrar perfis sem gender ou style
    incomplete_profiles = collection.find({
        "$or": [
            {"gender": {"$exists": False}},
            {"style": {"$exists": False}},
            {"name": {"$exists": False}}
        ]
    })
    
    updated_count = 0
    
    for profile in incomplete_profiles:
        updates = {}
        
        if "name" not in profile:
            updates["name"] = "Treinador Virtual"
            
        if "gender" not in profile:
             # Default seguro
            updates["gender"] = "Masculino"
            
        if "style" not in profile:
            # Default seguro
            updates["style"] = "Científico"
            
        if updates:
            print(f"Corrigindo perfil {profile['_id']} (User: {profile.get('user_email', 'Unknown')}): {updates}")
            collection.update_one(
                {"_id": profile["_id"]},
                {"$set": updates}
            )
            updated_count += 1
    
    print(f"\n✅ Migração de Perfis concluída! {updated_count} perfis corrigidos.")
    client.close()

if __name__ == "__main__":
    print("Iniciando verificação de integridade dos Trainer Profiles...")
    migrate_trainer_profiles()
