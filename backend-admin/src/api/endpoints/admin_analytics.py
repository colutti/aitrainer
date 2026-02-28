from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from src.core.deps import MainDB, CurrentAdmin

router = APIRouter(prefix="/admin/analytics", tags=["admin"])

@router.get("/overview")
def get_overview(_admin: CurrentAdmin, db: MainDB) -> dict:
    """KPIs gerais do sistema (lendo do banco principal)."""
    # Contar totais
    total_users = db.users.count_documents({})
    total_messages = db.message_store.count_documents({})
    total_workouts = db.workout_logs.count_documents({})
    total_nutrition_logs = db.nutrition_logs.count_documents({})

    # Usuários com mensagens
    active_users_total = len(db.message_store.distinct("SessionId"))

    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_users_7d = len(
        db.prompt_logs.distinct(
            "user_email", {"timestamp": {"$gte": seven_days_ago}}
        )
    )

    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    active_users_24h = len(
        db.prompt_logs.distinct(
            "user_email", {"timestamp": {"$gte": one_day_ago}}
        )
    )

    total_admins = db.users.count_documents({"role": "admin"})

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_messages": total_messages,
        "total_workouts": total_workouts,
        "total_nutrition_logs": total_nutrition_logs,
        "active_users_total": active_users_total,
        "active_users_7d": active_users_7d,
        "active_users_24h": active_users_24h,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/quality-metrics")
def get_quality_metrics(_admin: CurrentAdmin, db: MainDB) -> dict:
    """Métricas de qualidade do sistema."""
    # Média de mensagens por usuário
    avg_messages = _calculate_avg_messages(db)

    # Distribuição de trainers
    trainer_distribution = _calculate_trainer_distribution(db)

    # Distribuição de objetivos
    goal_distribution = _calculate_goal_distribution(db)

    # Usuários com treinos vs sem treinos
    users_with_workouts = len(db.workout_logs.distinct("user_email"))
    total_users = db.users.count_documents({})
    workout_engagement_rate = round(
        (users_with_workouts / total_users * 100) if total_users > 0 else 0, 2
    )

    # Usuários com nutrição vs sem nutrição
    users_with_nutrition = len(db.nutrition_logs.distinct("user_email"))
    nutrition_engagement_rate = round(
        (users_with_nutrition / total_users * 100) if total_users > 0 else 0, 2
    )

    return {
        "avg_messages_per_user": avg_messages,
        "trainer_distribution": trainer_distribution,
        "goal_distribution": goal_distribution,
        "workout_engagement_rate": workout_engagement_rate,
        "nutrition_engagement_rate": nutrition_engagement_rate,
        "users_with_workouts": users_with_workouts,
        "users_with_nutrition": users_with_nutrition,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def _calculate_avg_messages(db) -> float:
    try:
        pipeline = [
            {"$group": {"_id": "$SessionId", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}},
        ]
        result = list(db.message_store.aggregate(pipeline))
        return round(result[0]["avg"], 2) if result else 0.0
    except Exception: # pylint: disable=broad-exception-caught
        return 0.0

def _calculate_trainer_distribution(db) -> dict:
    try:
        pipeline = [{"$group": {"_id": "$trainer_type", "count": {"$sum": 1}}}]
        result = list(db.trainer_profiles.aggregate(pipeline))
        return {
            str(t["_id"]): t["count"] for t in result if t["_id"] is not None
        }
    except Exception: # pylint: disable=broad-exception-caught
        return {}

def _calculate_goal_distribution(db) -> dict:
    try:
        pipeline = [{"$group": {"_id": "$goal_type", "count": {"$sum": 1}}}]
        result = list(db.users.aggregate(pipeline))
        return {
            str(g["_id"]): g["count"] for g in result if g["_id"] is not None
        }
    except Exception: # pylint: disable=broad-exception-caught
        return {}
