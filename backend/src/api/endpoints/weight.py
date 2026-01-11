from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, Query
from src.services.auth import verify_token
from src.core.deps import get_ai_trainer_brain
from src.services.trainer import AITrainerBrain
from src.api.models.weight_log import WeightLog

router = APIRouter()

CurrentUser = Annotated[str, Depends(verify_token)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]

@router.post("")
def log_weight(
    log: WeightLog,
    user_email: CurrentUser,
    brain: AITrainerBrainDep
) -> dict:
    """
    Logs a weight entry for the user.
    If an entry exists for the same date, it updates it.
    """
    # Ensure usage of authenticated user email
    log.user_email = user_email
    
    # We need to access the database directly or add a method to brain.
    # Brain keeps business logic abstract.
    # Let's add weight methods to AITrainerBrain or verify if we should use DB directly here.
    # Looking at user.py, it uses `brain.save_user_profile`.
    # It's cleaner if Brain delegates to DB.
    # For now, let's assume we can access db via brain for consistency, 
    # OR we follow the pattern. 
    # Wait, `brain` is `AITrainerBrain`. Let's check `trainer.py`.
    # If `AITrainerBrain` just wraps DB, we should add methods there.
    # For speed in this phase, and since Brain is mostly for LLM/Trainer logic,
    # maybe accessing DB directly is acceptable if `AITrainerBrain` exposes it?
    # `AITrainerBrain` has `db` attribute? Let's check.
    # User endpoint: `brain.get_user_profile`
    # Let's assume we should update `AITrainerBrain` in `src/services/trainer.py` to forward calls.
    # Or, we can just inject database service if we want to decouple from "Brain" logic which implies AI.
    # But `get_ai_trainer_brain` is the main dependency.
    
    # Let's update Brain to support weight logging.
    doc_id, is_new = brain.db.save_weight_log(log)
    
    return {
        "message": "Weight logged successfully",
        "id": doc_id,
        "is_new": is_new,
        "date": log.date
    }

@router.get("")
def get_weight_logs(
    user_email: CurrentUser,
    brain: AITrainerBrainDep,
    limit: int = 30
) -> list[WeightLog]:
    """
    Retrieves recent weight logs for the user.
    """
    return brain.db.get_weight_logs(user_email=user_email, limit=limit)
