"""Endpoints for managing and viewing system prompt logs."""
from bson import ObjectId
from fastapi import APIRouter, Query, HTTPException
from src.core.deps import CURRENT_ADMIN_DEP, MAIN_DB_DEP

router = APIRouter(prefix="/admin/prompts", tags=["admin"])


def _detect_prompt_format(prompt_value: str) -> str:
    stripped = (prompt_value or "").strip()
    if not stripped:
        return "unknown"
    if stripped.startswith("#"):
        return "markdown"
    if "<" in stripped and ">" in stripped:
        return "xml_like"
    return "plain_text"


def _raw_tools_metrics(prompt_data: dict) -> tuple[int, list[str]]:
    tools_called = prompt_data.get("tools_called")
    called = tools_called if isinstance(tools_called, list) else []
    raw_tools = [
        name
        for name in called
        if isinstance(name, str) and name.endswith("_raw")
    ]
    return len(raw_tools), raw_tools

@router.get("/")
def list_prompts(
    _admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
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
            prompt_text = prompt_data.get("prompt", "")
            p["prompt_format"] = _detect_prompt_format(prompt_text)
            raw_count, raw_tools = _raw_tools_metrics(prompt_data)
            p["raw_tools_called_count"] = raw_count
            p["raw_tools_called"] = raw_tools

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
def get_prompt_details(
    prompt_id: str, _admin: CURRENT_ADMIN_DEP, db: MAIN_DB_DEP
) -> dict:
    """Retorna prompt completo sem truncamento."""
    try:
        prompt = db.prompt_logs.find_one({"_id": ObjectId(prompt_id)})
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid prompt ID") from exc

    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    prompt["_id"] = str(prompt["_id"])
    prompt_data = prompt.get("prompt", {})
    if isinstance(prompt_data, dict):
        prompt["prompt_format"] = _detect_prompt_format(prompt_data.get("prompt", ""))
        raw_count, raw_tools = _raw_tools_metrics(prompt_data)
        prompt["raw_tools_called_count"] = raw_count
        prompt["raw_tools_called"] = raw_tools
    return prompt
