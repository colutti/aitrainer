"""
Admin endpoints for user management.
Requires admin role for access.
"""

from typing import Annotated
from fastapi import APIRouter, Query, HTTPException, Depends
from src.core.auth import AdminUser
from src.core.config import settings
from src.core.deps import get_mongo_database, get_ai_trainer_brain, get_qdrant_client
from src.services.database import MongoDatabase
from src.services.trainer import AITrainerBrain
from src.core.logs import logger

router = APIRouter(prefix="/admin/users", tags=["admin"])

MongoDBDep = Annotated[MongoDatabase, Depends(get_mongo_database)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]


@router.get("/")
def list_users(
    admin_email: AdminUser,
    db: MongoDBDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict:
    """
    Lista usuários com paginação e busca.
    """
    logger.info(
        "Admin %s listing users (page=%s, search=%s)", admin_email, page, search
    )

    skip = (page - 1) * page_size
    query = {}

    if search:
        query = {"email": {"$regex": search, "$options": "i"}}

    # Buscar usuários (excluir senha e chaves sensíveis)
    users = list(
        db.users.collection.find(
            query,
            {"_id": 0, "password_hash": 0, "hevy_api_key": 0, "hevy_webhook_secret": 0},
        )
        .skip(skip)
        .limit(page_size)
    )

    total = db.users.collection.count_documents(query)

    return {
        "users": users,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{email}")
def get_user_details(email: str, admin_email: AdminUser, db: MongoDBDep) -> dict:
    """
    Retorna detalhes completos de um usuário específico.
    """
    logger.info("Admin %s viewing details for user %s", admin_email, email)

    user = db.users.get_profile(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Contar mensagens
    message_count = db.database["message_store"].count_documents({"SessionId": email})

    # Contar treinos
    workout_count = db.database["workout_logs"].count_documents({"user_email": email})

    # Contar logs de nutrição
    nutrition_count = db.database["nutrition"].count_documents({"user_email": email})

    # Sanitizar dados sensíveis
    profile_dict = user.model_dump(
        exclude={"password_hash", "hevy_api_key", "hevy_webhook_secret"}
    )

    return {
        "profile": profile_dict,
        "stats": {
            "message_count": message_count,
            "workout_count": workout_count,
            "nutrition_count": nutrition_count,
        },
    }


@router.patch("/{email}")
def update_user(
    email: str, updates: dict, admin_email: AdminUser, db: MongoDBDep
) -> dict:
    """
    Permite admin editar perfil de usuário.
    """
    logger.info(
        "Admin %s updating user %s: %s", admin_email, email, list(updates.keys())
    )

    # Campos protegidos que não podem ser modificados
    protected_fields = {"password_hash", "email"}
    for field in protected_fields:
        if field in updates:
            raise HTTPException(
                status_code=400, detail=f"Cannot modify protected field: {field}"
            )

    success = db.users.update_profile_fields(email, updates)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated successfully"}


@router.delete("/{email}")
def delete_user(email: str, admin_email: AdminUser, brain: AITrainerBrainDep) -> dict:
    """
    Deleta usuário completamente (MongoDB + Qdrant + logs).
    """
    logger.warning("Admin %s deleting user %s", admin_email, email)

    # Verificar se usuário existe
    user = brain.get_user_profile(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevenir deleção de outros admins (segurança)
    if user.role == "admin" and email != admin_email:
        raise HTTPException(status_code=400, detail="Cannot delete another admin user")

    try:
        # Deletar de todas as collections MongoDB
        db_mongo = brain.database.database

        db_mongo.users.delete_one({"email": email})
        db_mongo.trainer_profiles.delete_many({"email": email})
        db_mongo.chat_history.delete_many({"SessionId": email})
        db_mongo.workout_logs.delete_many({"user_email": email})
        db_mongo.nutrition.delete_many({"user_email": email})
        db_mongo.weights.delete_many({"user_email": email})
        db_mongo.prompt_logs.delete_many({"user_email": email})

        # Deletar coleção do Qdrant (memórias)
        qdrant = get_qdrant_client()
        collection_name = f"{settings.QDRANT_COLLECTION_NAME}_{email}"

        try:
            qdrant.delete_collection(collection_name)
            logger.info("Deleted Qdrant collection: %s", collection_name)
        except Exception as q_error:  # pylint: disable=broad-exception-caught
            logger.warning(
                "Could not delete Qdrant collection %s: %s", collection_name, q_error
            )

        logger.info("User %s deleted completely by admin %s", email, admin_email)

        return {
            "message": f"User {email} deleted successfully",
            "deleted_from": [
                "users", "trainer_profiles", "chat_history", "workout_logs",
                "nutrition", "weights", "prompt_logs", "qdrant",
            ],
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error deleting user %s: %s", email, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete user: {str(e)}"
        ) from e
