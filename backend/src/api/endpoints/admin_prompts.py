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


@router.get("/")
def list_prompts(
    admin_email: AdminUser,
    db: MongoDBDep,
    user_id: str | None = Query(None, alias="user_id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict:
    """
    Lista prompts logados (collection: prompt_logs).
    """
    logger.info(
        "Admin %s listing prompts (page=%s, user=%s)", admin_email, page, user_id
    )

    query = {}
    if user_id:
        query = {"user_email": user_id}

    skip = (page - 1) * page_size

    # Buscar prompts
    prompts_cursor = (
        db.prompts.collection.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(page_size)
    )
    prompts = list(prompts_cursor)

    # Truncar conteúdo longo e achatar campos para o frontend
    for p in prompts:
        # Converter ObjectId para string
        if "_id" in p:
            p["id"] = str(p["_id"])
            p["_id"] = str(p["_id"])

        # Campos que o frontend espera no nível superior
        p["model"] = "unknown"
        p["tokens_input"] = 0
        p["tokens_output"] = 0
        p["duration_ms"] = 0
        p["status"] = "success"
        p["prompt_name"] = "N/A"

        if "prompt" in p and isinstance(p["prompt"], dict):
            prompt_data = p["prompt"]

            # Tentar extrair metadados se existirem
            p["model"] = prompt_data.get("model", p["model"])
            p["tokens_input"] = prompt_data.get("tokens_input", p["tokens_input"])
            p["tokens_output"] = prompt_data.get("tokens_output", p["tokens_output"])
            p["duration_ms"] = prompt_data.get("duration_ms", p["duration_ms"])
            p["status"] = prompt_data.get("status", p["status"])
            p["prompt_name"] = prompt_data.get("prompt_name", p["prompt_name"])

            # Preview logic
            _process_prompt_preview(p, prompt_data)

    total = db.prompts.collection.count_documents(query)

    return {
        "prompts": prompts,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
    }


def _process_prompt_preview(p: dict, prompt_data: dict):
    """Helper to process prompt preview logic."""
    if "messages" in prompt_data:
        messages = prompt_data["messages"]
        p["messages_count"] = len(messages) if isinstance(messages, list) else 0
        p["messages_preview"] = (
            str(messages[0].get("content", ""))[:200] + "..."
            if messages
            and isinstance(messages, list)
            and isinstance(messages[0], dict)
            else ""
        )
    elif "input" in prompt_data:
        input_val = prompt_data.get("input", "")
        p["messages_count"] = 1
        p["messages_preview"] = str(input_val)[:200] + "..."
    elif "prompt" in prompt_data:
        prompt_str = prompt_data.get("prompt", "")
        p["messages_count"] = 1
        p["messages_preview"] = str(prompt_str)[:200] + "..."
    else:
        p["messages_count"] = 0
        p["messages_preview"] = "Estrutura não reconhecida"


@router.get("/{prompt_id}")
def get_prompt_details(prompt_id: str, admin_email: AdminUser, db: MongoDBDep) -> dict:
    """
    Retorna prompt completo sem truncamento.
    """
    logger.info("Admin %s viewing prompt %s", admin_email, prompt_id)

    try:
        prompt = db.prompts.collection.find_one({"_id": ObjectId(prompt_id)})
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Invalid ObjectId: %s", prompt_id)
        raise HTTPException(
            status_code=400, detail=f"Invalid prompt ID: {str(e)}"
        ) from e

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Converter ObjectId para string
    prompt["_id"] = str(prompt["_id"])

    return prompt
