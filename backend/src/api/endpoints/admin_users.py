"""
Admin endpoints for user management.
Requires admin role for access.
"""

from typing import Annotated
from fastapi import APIRouter, Query, HTTPException, Depends
from src.core.auth import AdminUser
from src.core.deps import get_mongo_database, get_ai_trainer_brain
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
    search: str | None = None
) -> dict:
    """
    Lista usuários com paginação e busca.

    Args:
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance
        page: Número da página (começa em 1)
        page_size: Quantidade de usuários por página
        search: Filtro de busca por email (opcional)

    Returns:
        dict: Contém users, total, page e total_pages
    """
    logger.info(f"Admin {admin_email} listing users (page={page}, search={search})")

    skip = (page - 1) * page_size
    query = {}

    if search:
        query = {"email": {"$regex": search, "$options": "i"}}

    # Buscar usuários (excluir senha e chaves sensíveis)
    users = list(db.users.collection.find(
        query,
        {
            "_id": 0,
            "password_hash": 0,
            "hevy_api_key": 0,
            "hevy_webhook_secret": 0
        }
    ).skip(skip).limit(page_size))

    total = db.users.collection.count_documents(query)

    return {
        "users": users,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{email}")
def get_user_details(
    email: str,
    admin_email: AdminUser,
    db: MongoDBDep
) -> dict:
    """
    Retorna detalhes completos de um usuário específico.

    Args:
        email: Email do usuário a buscar
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance

    Returns:
        dict: Contém profile e stats do usuário

    Raises:
        HTTPException: 404 se usuário não encontrado
    """
    logger.info(f"Admin {admin_email} viewing details for user {email}")

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
    profile_dict = user.model_dump(exclude={
        "password_hash",
        "hevy_api_key",
        "hevy_webhook_secret"
    })

    return {
        "profile": profile_dict,
        "stats": {
            "message_count": message_count,
            "workout_count": workout_count,
            "nutrition_count": nutrition_count
        }
    }


@router.patch("/{email}")
def update_user(
    email: str,
    updates: dict,
    admin_email: AdminUser,
    db: MongoDBDep
) -> dict:
    """
    Permite admin editar perfil de usuário.

    Args:
        email: Email do usuário a atualizar
        updates: Dicionário com campos a atualizar
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance

    Returns:
        dict: Mensagem de sucesso

    Raises:
        HTTPException: 404 se usuário não encontrado
        HTTPException: 400 se tentar modificar campos protegidos
    """
    logger.info(f"Admin {admin_email} updating user {email}: {list(updates.keys())}")

    # Campos protegidos que não podem ser modificados
    protected_fields = {"password_hash", "email"}
    for field in protected_fields:
        if field in updates:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot modify protected field: {field}"
            )

    success = db.users.update_profile_fields(email, updates)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated successfully"}


@router.delete("/{email}")
def delete_user(
    email: str,
    admin_email: AdminUser,
    brain: AITrainerBrainDep
) -> dict:
    """
    Deleta usuário completamente (MongoDB + Qdrant + logs).

    Args:
        email: Email do usuário a deletar
        admin_email: Email do admin (verificado por dependency)
        brain: AI Trainer Brain instance

    Returns:
        dict: Mensagem de sucesso

    Raises:
        HTTPException: 404 se usuário não encontrado
        HTTPException: 400 se tentar deletar outro admin
    """
    logger.warning(f"Admin {admin_email} deleting user {email}")

    # Verificar se usuário existe
    user = brain.get_user_profile(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevenir deleção de outros admins (segurança)
    if user.role == "admin" and email != admin_email:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete another admin user"
        )

    try:
        # Deletar de todas as collections MongoDB
        db = brain.database.database

        db.users.delete_one({"email": email})
        db.trainer_profiles.delete_many({"email": email})
        db.chat_history.delete_many({"SessionId": email})
        db.workout_logs.delete_many({"user_email": email})
        db.nutrition.delete_many({"user_email": email})
        db.weights.delete_many({"user_email": email})
        db.prompt_logs.delete_many({"user_email": email})

        # Deletar coleção do Qdrant (memórias)
        from src.core.config import settings
        from src.core.deps import get_qdrant_client

        qdrant = get_qdrant_client()
        collection_name = f"{settings.QDRANT_COLLECTION_NAME}_{email}"

        try:
            qdrant.delete_collection(collection_name)
            logger.info(f"Deleted Qdrant collection: {collection_name}")
        except Exception as e:
            logger.warning(f"Could not delete Qdrant collection {collection_name}: {e}")

        logger.info(f"User {email} deleted completely by admin {admin_email}")

        return {
            "message": f"User {email} deleted successfully",
            "deleted_from": [
                "users",
                "trainer_profiles",
                "chat_history",
                "workout_logs",
                "nutrition",
                "weights",
                "prompt_logs",
                "qdrant"
            ]
        }

    except Exception as e:
        logger.error(f"Error deleting user {email}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )
