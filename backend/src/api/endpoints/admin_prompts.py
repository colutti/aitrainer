"""
Admin endpoints for prompts management.
Requires admin role for access.
"""

from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException, Depends
from src.core.auth import AdminUser
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.core.logs import logger

router = APIRouter(prefix="/admin/prompts", tags=["admin"])

MongoDBDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.get("/list")
def list_prompts(
    admin_email: AdminUser,
    db: MongoDBDep,
    user_email: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
) -> dict:
    """
    Lista prompts logados (collection: prompt_logs).

    Args:
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance
        user_email: Filtrar por email do usuário (opcional)
        page: Número da página
        page_size: Quantidade de prompts por página

    Returns:
        dict: Contém prompts, total, page e total_pages
    """
    logger.info(f"Admin {admin_email} listing prompts (page={page}, user={user_email})")

    query = {}
    if user_email:
        query = {"user_email": user_email}

    skip = (page - 1) * page_size

    # Buscar prompts
    prompts = list(db.prompts.collection.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(page_size))

    # Truncar conteúdo longo para economizar bandwidth
    for p in prompts:
        # Converter ObjectId para string
        if "_id" in p:
            p["_id"] = str(p["_id"])

        if "prompt" in p:
            prompt_type = p["prompt"].get("type", "")

            # Para prompts "with_tools" - tem campo messages
            if "messages" in p["prompt"]:
                messages = p["prompt"]["messages"]
                if messages and len(messages) > 0:
                    p["prompt"]["messages_count"] = len(messages)
                    # Preview da primeira mensagem
                    first_msg = messages[0]
                    if isinstance(first_msg, dict) and "content" in first_msg:
                        content = first_msg.get("content", "")
                        p["prompt"]["messages_preview"] = content[:200] + "..." if len(content) > 200 else content
                    # Remover array completo para economizar bandwidth
                    p["prompt"]["messages"] = []
                else:
                    p["prompt"]["messages_count"] = 0
                    p["prompt"]["messages_preview"] = ""

            # Para prompts "simple" - tem campo input
            elif "input" in p["prompt"]:
                input_data = p["prompt"]["input"]

                # Verificar se tem new_lines
                if "new_lines" in input_data and input_data["new_lines"]:
                    new_lines = input_data["new_lines"]
                    # Contar "mensagens" no new_lines (separadas por linhas de timestamp)
                    lines_count = new_lines.count("[") if "[" in new_lines else 1
                    p["prompt"]["messages_count"] = lines_count
                    p["prompt"]["messages_preview"] = new_lines[:200] + "..." if len(new_lines) > 200 else new_lines

                # Ou se tem user_prompt_content
                elif "user_prompt_content" in input_data and input_data["user_prompt_content"]:
                    content = input_data["user_prompt_content"]
                    p["prompt"]["messages_count"] = 1  # Considera como 1 mensagem do usuário
                    p["prompt"]["messages_preview"] = content[:200] + "..." if len(content) > 200 else content

                # Sem conteúdo útil
                else:
                    p["prompt"]["messages_count"] = 0
                    p["prompt"]["messages_preview"] = "Sem conteúdo"

            # Fallback para prompts V3 que tem apenas o campo 'prompt' (string renderizada)
            elif "prompt" in p["prompt"]:
                prompt_str = p["prompt"]["prompt"]
                p["prompt"]["messages_count"] = 1
                p["prompt"]["messages_preview"] = prompt_str[:200] + "..." if len(prompt_str) > 200 else prompt_str

            # Fallback para outros tipos ou estrutura desconhecida
            else:
                p["prompt"] = p.get("prompt") or {}
                p["prompt"]["messages_count"] = 0
                p["prompt"]["messages_preview"] = "Estrutura não reconhecida"

    total = db.prompts.collection.count_documents(query)

    return {
        "prompts": prompts,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/{prompt_id}")
def get_prompt_details(
    prompt_id: str,
    admin_email: AdminUser,
    db: MongoDBDep
) -> dict:
    """
    Retorna prompt completo sem truncamento.

    Args:
        prompt_id: ID do prompt (ObjectId como string)
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance

    Returns:
        dict: Prompt completo

    Raises:
        HTTPException: 400 se ID inválido
        HTTPException: 404 se prompt não encontrado
    """
    logger.info(f"Admin {admin_email} viewing prompt {prompt_id}")

    try:
        prompt = db.prompts.collection.find_one({"_id": ObjectId(prompt_id)})
    except Exception as e:
        logger.error(f"Invalid ObjectId: {prompt_id}")
        raise HTTPException(status_code=400, detail=f"Invalid prompt ID: {str(e)}")

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Converter ObjectId para string
    prompt["_id"] = str(prompt["_id"])

    return prompt
