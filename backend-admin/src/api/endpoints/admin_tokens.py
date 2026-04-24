"""Endpoints for managing and analyzing token usage and costs."""
# pyright: reportArgumentType=false
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import APIRouter, Query
from src.core.deps import CURRENT_ADMIN_DEP, MAIN_DB_DEP

router = APIRouter(prefix="/admin/tokens", tags=["admin"])

def _format_token_item(item: Any) -> dict[str, Any]:
    """Helper to format a single token usage item for the summary response."""
    user_email = str(item.get("_id", "unknown"))
    requested_model = str(item.get("requested_model", ""))
    resolved_model = str(item.get("resolved_model", ""))
    resolved_provider = item.get("resolved_provider")
    total_input = int(item.get("total_input", 0))
    total_output = int(item.get("total_output", 0))
    cost_usd = float(item.get("total_cost", 0.0))
    last_activity_val = item.get("last_activity")
    last_activity_str = ""
    if isinstance(last_activity_val, datetime):
        last_activity_str = last_activity_val.isoformat()

    return {
        "user_email": user_email,
        "total_input": total_input,
        "total_output": total_output,
        "message_count": int(item.get("message_count", 0)),
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "resolved_provider": resolved_provider,
        "cost_usd": cost_usd,
        "last_activity": last_activity_str
    }

@router.get("/summary")
def get_token_summary(
    _admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
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
            "requested_model": {"$last": "$requested_model"},
            "resolved_model": {"$last": "$resolved_model"},
            "resolved_provider": {"$last": "$resolved_provider"},
            "total_cost": {"$sum": {"$ifNull": ["$usage_cost", 0]}},
            "last_activity": {"$max": "$timestamp"}
        }},
        {"$sort": {"total_input": -1}}
    ]

    results = list(db.prompt_logs.aggregate(pipeline))
    final_results: Any = []
    for item in results:
        final_results.append(_format_token_item(item))  # type: ignore

    return {
        "data": final_results,
        "days": days,
        "total_users_with_tokens": len(results),
    }

@router.get("/timeseries")
def get_token_timeseries(
    _admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
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
