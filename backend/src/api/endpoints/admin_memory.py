"""
Admin endpoints for memory and messages management.
Requires admin role for access.
"""

from typing import Annotated
from fastapi import APIRouter, Query, HTTPException, Depends
from qdrant_client import QdrantClient

from src.core.auth import AdminUser
from src.core.deps import get_mongo_database, get_ai_trainer_brain, get_qdrant_client
from src.services.database import MongoDatabase
from src.services.trainer import AITrainerBrain
from src.core.config import settings
from src.core.logs import logger

router = APIRouter(prefix="/admin/memory", tags=["admin"])

MongoDBDep = Annotated[MongoDatabase, Depends(get_mongo_database)]
AITrainerBrainDep = Annotated[AITrainerBrain, Depends(get_ai_trainer_brain)]
QdrantClientDep = Annotated[QdrantClient, Depends(get_qdrant_client)]


@router.get("/{user_email}/messages")
def get_user_messages(
    user_email: str,
    admin_email: AdminUser,
    db: MongoDBDep,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    """
    Lista mensagens de chat de um usuário.
    """
    logger.info("Admin %s viewing messages for user %s", admin_email, user_email)

    # Verificar se usuário existe
    user = db.users.get_profile(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Buscar mensagens
    history = db.chat.get_history(user_email, limit=limit)

    return {
        "messages": [msg.model_dump() for msg in history],
        "total": len(history),
        "user_email": user_email,
    }


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
@router.get("/{user_email}/memories")
def get_user_memories(
    user_email: str,
    admin_email: AdminUser,
    db: MongoDBDep,
    qdrant: QdrantClientDep,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict:
    """
    Lista memórias Qdrant de um usuário.
    """
    logger.info(
        "Admin %s viewing memories for user %s (page=%s)",
        admin_email, user_email, page
    )

    # Verificar se usuário existe
    user = db.users.get_profile(user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        # Coleção Qdrant é por usuário
        collection_name = f"{settings.QDRANT_COLLECTION_NAME}_{user_email}"

        # Verificar se coleção existe
        collections = qdrant.get_collections().collections
        collection_exists = any(c.name == collection_name for c in collections)

        if not collection_exists:
            return {
                "memories": [],
                "total": 0,
                "page": page,
                "total_pages": 0,
                "message": f"No memories found for user {user_email}",
            }

        # Scroll através das memórias (Qdrant não tem paginação direta)
        offset = (page - 1) * page_size

        # Buscar memórias
        scroll_result = qdrant.scroll(
            collection_name=collection_name,
            limit=page_size,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        points, _ = scroll_result

        # Formatar memórias
        memories = []
        for point in points:
            payload = point.payload or {}
            memory = {
                "id": str(point.id),
                "memory": payload.get("memory", ""),
                "created_at": payload.get("created_at"),
                "updated_at": payload.get("updated_at"),
                "user_id": payload.get("user_id"),
            }
            memories.append(memory)

        # Contar total (aproximado via collection info)
        collection_info = qdrant.get_collection(collection_name)
        total = collection_info.points_count or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "memories": memories,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "user_email": user_email,
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error fetching memories for %s: %s", user_email, e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch memories: {str(e)}"
        ) from e
