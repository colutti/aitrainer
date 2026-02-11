"""
Admin endpoints for analytics and quality metrics.
Requires admin role for access.
"""

from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from src.core.auth import AdminUser
from src.core.deps import get_mongo_database
from src.services.database import MongoDatabase
from src.core.logs import logger

router = APIRouter(prefix="/admin/analytics", tags=["admin"])

MongoDBDep = Annotated[MongoDatabase, Depends(get_mongo_database)]


@router.get("/overview")
def get_overview(admin_email: AdminUser, db: MongoDBDep) -> dict:
    """
    KPIs gerais do sistema.
    """
    logger.info("Admin %s requesting system overview", admin_email)

    database = db.database

    # Contar totais
    total_users = database.users.count_documents({})
    total_messages = database.message_store.count_documents({})
    total_workouts = database.workout_logs.count_documents({})
    total_nutrition_logs = database.nutrition_logs.count_documents({})

    # Usuários com mensagens
    active_users_total = len(database.message_store.distinct("SessionId"))

    # Para usuários ativos recentes, usamos prompt_logs que tem timestamp
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    active_users_7d = len(
        database.prompt_logs.distinct(
            "user_email", {"timestamp": {"$gte": seven_days_ago}}
        )
    )

    # Usuários ativos nas últimas 24 horas
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)
    active_users_24h = len(
        database.prompt_logs.distinct(
            "user_email", {"timestamp": {"$gte": one_day_ago}}
        )
    )

    # Contar admins
    total_admins = database.users.count_documents({"role": "admin"})

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


# pylint: disable=too-many-locals
@router.get("/quality-metrics")
def get_quality_metrics(admin_email: AdminUser, db: MongoDBDep) -> dict:
    """
    Métricas de qualidade do sistema.
    """
    logger.info("Admin %s requesting quality metrics", admin_email)

    database = db.database

    # Média de mensagens por usuário
    avg_messages = _calculate_avg_messages(database)

    # Distribuição de trainers
    trainer_distribution = _calculate_trainer_distribution(database)

    # Distribuição de objetivos
    goal_distribution = _calculate_goal_distribution(database)

    # Usuários com treinos vs sem treinos
    users_with_workouts = len(database.workout_logs.distinct("user_email"))
    total_users = database.users.count_documents({})
    workout_engagement_rate = round(
        (users_with_workouts / total_users * 100) if total_users > 0 else 0, 2
    )

    # Usuários com nutrição vs sem nutrição
    users_with_nutrition = len(database.nutrition_logs.distinct("user_email"))
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


def _calculate_avg_messages(database) -> float:
    """Helper to calculate average messages per user."""
    try:
        pipeline = [
            {"$group": {"_id": "$SessionId", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}},
        ]
        result = list(database.message_store.aggregate(pipeline))
        return round(result[0]["avg"], 2) if result else 0.0
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error calculating avg messages: %s", e)
        return 0.0


def _calculate_trainer_distribution(database) -> dict:
    """Helper to calculate trainer distribution."""
    try:
        pipeline = [{"$group": {"_id": "$trainer_type", "count": {"$sum": 1}}}]
        result = list(database.trainer_profiles.aggregate(pipeline))
        return {
            t["_id"]: t["count"] for t in result if t["_id"] is not None
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error calculating trainer distribution: %s", e)
        return {}


def _calculate_goal_distribution(database) -> dict:
    """Helper to calculate goal distribution."""
    try:
        pipeline = [{"$group": {"_id": "$goal_type", "count": {"$sum": 1}}}]
        result = list(database.users.aggregate(pipeline))
        return {
            g["_id"]: g["count"] for g in result if g["_id"] is not None
        }
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error calculating goal distribution: %s", e)
        return {}
