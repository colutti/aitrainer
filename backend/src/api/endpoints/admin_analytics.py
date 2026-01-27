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
def get_overview(
    admin_email: AdminUser,
    db: MongoDBDep
) -> dict:
    """
    KPIs gerais do sistema.

    Args:
        admin_email: Email do admin (verificado por dependency)
        db: MongoDB database instance

    Returns:
        dict: Métricas gerais do sistema
    """
    logger.info(f"Admin {admin_email} requesting system overview")

    database = db.database

    # Contar totais
    total_users = database.users.count_documents({})
    total_messages = database.message_store.count_documents({})
    total_workouts = database.workout_logs.count_documents({})
    total_nutrition_logs = database.nutrition_logs.count_documents({})

    # Usuários com mensagens (message_store não tem campo timestamp no nível superior)
    # Contamos apenas usuários únicos que já enviaram mensagens
    active_users_total = len(database.message_store.distinct("SessionId"))

    # Para usuários ativos recentes, usamos prompt_logs que tem timestamp
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    active_users_7d = len(database.prompt_logs.distinct(
        "user_email",
        {"timestamp": {"$gte": seven_days_ago}}
    ))

    # Usuários ativos nas últimas 24 horas
    one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)

    active_users_24h = len(database.prompt_logs.distinct(
        "user_email",
        {"timestamp": {"$gte": one_day_ago}}
    ))

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
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/quality-metrics")
def get_quality_metrics(
    admin_email: AdminUser,
    db: MongoDBDep
) -> dict:
    """
    Métricas de qualidade do sistema.

    Args:
        admin_email: Email do admin (verificado by dependency)
        db: MongoDB database instance

    Returns:
        dict: Métricas de qualidade (avg messages, trainer distribution, etc)
    """
    logger.info(f"Admin {admin_email} requesting quality metrics")

    database = db.database

    # Média de mensagens por usuário
    try:
        pipeline = [
            {"$group": {"_id": "$SessionId", "count": {"$sum": 1}}},
            {"$group": {"_id": None, "avg": {"$avg": "$count"}}}
        ]
        result = list(database.message_store.aggregate(pipeline))
        avg_messages = round(result[0]['avg'], 2) if result else 0
    except Exception as e:
        logger.error(f"Error calculating avg messages: {e}")
        avg_messages = 0

    # Distribuição de trainers
    try:
        pipeline = [
            {"$group": {"_id": "$trainer_type", "count": {"$sum": 1}}}
        ]
        trainer_dist_result = list(database.trainer_profiles.aggregate(pipeline))
        trainer_distribution = {
            t['_id']: t['count']
            for t in trainer_dist_result
            if t['_id'] is not None
        }
    except Exception as e:
        logger.error(f"Error calculating trainer distribution: {e}")
        trainer_distribution = {}

    # Distribuição de objetivos
    try:
        pipeline = [
            {"$group": {"_id": "$goal_type", "count": {"$sum": 1}}}
        ]
        goal_dist_result = list(database.users.aggregate(pipeline))
        goal_distribution = {
            g['_id']: g['count']
            for g in goal_dist_result
            if g['_id'] is not None
        }
    except Exception as e:
        logger.error(f"Error calculating goal distribution: {e}")
        goal_distribution = {}

    # Usuários com treinos vs sem treinos
    users_with_workouts = len(database.workout_logs.distinct("user_email"))
    total_users = database.users.count_documents({})
    workout_engagement_rate = round(
        (users_with_workouts / total_users * 100) if total_users > 0 else 0,
        2
    )

    # Usuários com nutrição vs sem nutrição
    users_with_nutrition = len(database.nutrition_logs.distinct("user_email"))
    nutrition_engagement_rate = round(
        (users_with_nutrition / total_users * 100) if total_users > 0 else 0,
        2
    )

    return {
        "avg_messages_per_user": avg_messages,
        "trainer_distribution": trainer_distribution,
        "goal_distribution": goal_distribution,
        "workout_engagement_rate": workout_engagement_rate,
        "nutrition_engagement_rate": nutrition_engagement_rate,
        "users_with_workouts": users_with_workouts,
        "users_with_nutrition": users_with_nutrition,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
