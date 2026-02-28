from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException
from src.core.deps import MainDB, CurrentAdmin

router = APIRouter(prefix="/admin/prompts", tags=["admin"])

@router.get("/")
def list_prompts(
    _admin: CurrentAdmin,
    db: MainDB,
    user_id: str | None = Query(None, alias="user_id"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
) -> dict:
    """Lista prompts logados."""
    query = {}
    if user_id:
        query = {"user_email": user_id}

    skip = (page - 1) * page_size

    prompts_cursor = (
        db.prompt_logs.find(query)
        .sort("timestamp", -1)
        .skip(skip)
        .limit(page_size)
    )
    prompts = list(prompts_cursor)

    for p in prompts:
        if "_id" in p:
            p["id"] = str(p["_id"])
            p["_id"] = str(p["_id"])

        # Campos basicos para o frontend
        p["model"] = p.get("model", "unknown")
        p["tokens_input"] = p.get("tokens_input", 0)
        p["tokens_output"] = p.get("tokens_output", 0)
        p["duration_ms"] = p.get("duration_ms", 0)
        p["status"] = p.get("status", "success")
        p["prompt_name"] = p.get("prompt_name", "N/A")

        if "prompt" in p and isinstance(p["prompt"], dict):
            prompt_data = p["prompt"]
            if "messages" in prompt_data:
                messages = prompt_data["messages"]
                p["messages_count"] = len(messages) if isinstance(messages, list) else 0
                p["messages_preview"] = (
                    str(messages[0].get("content", ""))[:200] + "..."
                    if messages and isinstance(messages, list) and isinstance(messages[0], dict)
                    else ""
                )
            else:
                p["messages_count"] = 1
                p["messages_preview"] = str(prompt_data.get("input", "N/A"))[:200]

    total = db.prompt_logs.count_documents(query)

    return {
        "prompts": prompts,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
    }

@router.get("/{prompt_id}")
def get_prompt_details(prompt_id: str, _admin: CurrentAdmin, db: MainDB) -> dict:
    """Retorna prompt completo sem truncamento."""
    try:
        prompt = db.prompt_logs.find_one({"_id": ObjectId(prompt_id)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid prompt ID") from exc

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt["_id"] = str(prompt["_id"])
    return prompt
