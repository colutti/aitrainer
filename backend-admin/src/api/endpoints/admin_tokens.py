from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from src.core.deps import MainDB, CurrentAdmin

router = APIRouter(prefix="/admin/tokens", tags=["admin"])

# Quick cost calculation helper
PRICING = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "claude-3-5-sonnet-20240620": {"input": 0.003, "output": 0.015},
    "gemini-1.5-pro": {"input": 0.0035, "output": 0.0105},
}

def get_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = PRICING.get(model, PRICING["gpt-4o-mini"])
    return (input_tokens / 1000 * rates["input"]) + (output_tokens / 1000 * rates["output"])

@router.get("/summary")
def get_token_summary(
    _admin: CurrentAdmin,
    db: MainDB,
    days: int = Query(30, ge=1, le=365),
) -> dict:
    """Consumo de tokens por usuário."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": since}}},
        {"$group": {
            "_id": "$user_email",
            "total_input": {"$sum": "$tokens_input"},
            "total_output": {"$sum": "$tokens_output"},
            "message_count": {"$sum": 1},
            "model": {"$first": "$model"},
            "last_activity": {"$max": "$timestamp"}
        }},
        {"$sort": {"total_input": -1}}
    ]
    
    results = list(db.prompt_logs.aggregate(pipeline))
    
    for item in results:
        item["user_email"] = item["_id"]
        item["cost_usd"] = get_cost_usd(item.get("model", ""), item.get("total_input", 0), item.get("total_output", 0))
        # Ensure last_activity is ISO string for frontend
        if isinstance(item.get("last_activity"), datetime):
            item["last_activity"] = item["last_activity"].isoformat()

    return {
        "data": results,
        "days": days,
        "total_users_with_tokens": len(results),
    }

@router.get("/timeseries")
def get_token_timeseries(
    _admin: CurrentAdmin,
    db: MainDB,
    days: int = Query(30, ge=1, le=365),
    user_email: str | None = Query(None),
) -> dict:
    """Dados temporais de consumo de tokens para o gráfico."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    
    match_query = {"timestamp": {"$gte": since}}
    if user_email:
        match_query["user_email"] = user_email

    pipeline = [
        {"$match": match_query},
        {"$project": {
            "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "tokens_input": 1,
            "tokens_output": 1
        }},
        {"$group": {
            "_id": "$date",
            "tokens_input": {"$sum": "$tokens_input"},
            "tokens_output": {"$sum": "$tokens_output"},
            "count": {"$sum": 1}
        }},
        {"$project": {
            "_id": 0,
            "date": "$_id",
            "tokens_input": 1,
            "tokens_output": 1,
            "count": 1
        }},
        {"$sort": {"date": 1}}
    ]
    
    results = list(db.prompt_logs.aggregate(pipeline))
    return {
        "data": results,
        "days": days,
        "user_email": user_email,
        "data_points": len(results),
    }
