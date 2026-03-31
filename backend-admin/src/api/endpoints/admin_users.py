"""Endpoints for administrative user management tasks (list, update, delete)."""
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from src.core.deps import CURRENT_ADMIN_DEP, MAIN_DB_DEP

router = APIRouter(prefix="/admin/users", tags=["admin"])
DEMO_READ_ONLY_DETAIL = "demo_read_only"


def _latest_demo_snapshot(db, email: str) -> dict | None:
    snapshot = db.demo_snapshots.find_one(
        {"demo_email": email},
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    return snapshot


def _published_demo_episodes(db, email: str) -> list[dict]:
    cursor = db.demo_episodes.find(
        {"demo_email": email},
        {"_id": 0},
    ).sort("started_at", 1)
    return [episode for episode in cursor if episode.get("status", "published") == "published"]


@router.get("/")
def list_users(
    _admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str | None = None,
) -> dict:
    """Lista usuários com paginação e busca."""
    skip = (page - 1) * page_size
    query = {}

    if search:
        query = {"email": {"$regex": search, "$options": "i"}}

    # Buscar usuários (excluir campos sensíveis)
    exclude_fields = {
        "_id": 0,
        "password_hash": 0,
        "hevy_api_key": 0,
        "photo_base64": 0
    }
    users = list(
        db.users.find(query, exclude_fields)
        .skip(skip)
        .limit(page_size)
    )

    total = db.users.count_documents(query)

    return {
        "users": users,
        "total": total,
        "page": page,
        "total_pages": (total + page_size - 1) // page_size,
    }

@router.get("/{email}")
def get_user_details(email: str, _admin: CURRENT_ADMIN_DEP, db: MAIN_DB_DEP) -> dict:
    """Retorna detalhes completos de um usuário específico."""
    user = db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Contar mensagens
    message_count = db.message_store.count_documents({"SessionId": email})

    # Contar treinos
    workout_count = db.workout_logs.count_documents({"user_email": email})

    # Contar logs de nutrição
    nutrition_count = db.nutrition_logs.count_documents({"user_email": email})

    # Sanitizar dados sensíveis
    user.pop("_id", None)
    user.pop("password_hash", None)
    user.pop("hevy_api_key", None)

    response = {
        "profile": user,
        "stats": {
            "message_count": message_count,
            "workout_count": workout_count,
            "nutrition_count": nutrition_count,
        },
    }
    if user.get("is_demo"):
        demo_episodes = _published_demo_episodes(db, email)
        response["demo_snapshot"] = _latest_demo_snapshot(db, email)
        if response["demo_snapshot"]:
            response["demo_snapshot"]["episode_count"] = len(demo_episodes)
            response["demo_snapshot"]["message_count"] = db.demo_messages.count_documents(
                {"demo_email": email, "status": "published"}
            )
        response["demo_episodes"] = demo_episodes
    return response


@router.get("/{email}/demo-episodes/{episode_id}")
def get_demo_episode(
    email: str,
    episode_id: str,
    _admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
) -> dict:
    """Retorna detalhes de um episódio publicado no demo."""
    episode = db.demo_episodes.find_one(
        {"demo_email": email, "episode_id": episode_id},
        {"_id": 0},
    )
    if not episode or episode.get("status") != "published":
        raise HTTPException(status_code=404, detail="Demo episode not found")

    messages = list(
        db.demo_messages.find(
            {
                "demo_email": email,
                "episode_id": episode_id,
                "status": "published",
            },
            {"_id": 0},
        ).sort("timestamp", 1)
    )
    return {"episode": episode, "messages": messages}

@router.patch("/{email}")
def update_user(
    email: str, updates: dict, _admin: CURRENT_ADMIN_DEP, db: MAIN_DB_DEP
) -> dict:
    """Permite admin editar perfil de usuário."""
    # Campos protegidos
    protected_fields = {"password_hash", "email"}
    for field in protected_fields:
        if field in updates:
            raise HTTPException(
                status_code=400, detail=f"Cannot modify protected field: {field}"
            )
    target_user = db.users.find_one({"email": email}, {"is_demo": 1})
    if target_user and target_user.get("is_demo"):
        raise HTTPException(status_code=403, detail=DEMO_READ_ONLY_DETAIL)

    # Lógica de reset se mudar o plano
    if "subscription_plan" in updates:
        now = datetime.now()
        updates["current_billing_cycle_start"] = now
        updates["messages_sent_this_month"] = 0
        updates["messages_sent_today"] = 0
        updates["stripe_subscription_status"] = "active" # Override manually
        # Se for um override manual, limpamos o stripe_subscription_id pra evitar conflitos
        if "stripe_subscription_id" not in updates:
            updates["stripe_subscription_id"] = None

    result = db.users.update_one({"email": email}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User updated successfully"}

@router.delete("/{email}")
def delete_user(email: str, admin: CURRENT_ADMIN_DEP, db: MAIN_DB_DEP) -> dict:
    """Deleta usuário completamente (MongoDB + logs)."""
    # Prevenir deleção de outros admins (segurança rápida baseada no email do admin logado)
    target_user = db.users.find_one({"email": email})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    admin_email = admin.get("email") if admin else None
    if target_user.get("role") == "admin" and email != admin_email:
        raise HTTPException(status_code=403, detail="Cannot delete another admin user")
    if target_user.get("is_demo"):
        raise HTTPException(status_code=403, detail=DEMO_READ_ONLY_DETAIL)

    # Deletar de todas as collections
    db.users.delete_one({"email": email})
    db.trainer_profiles.delete_many({"email": email})
    db.message_store.delete_many({"SessionId": email})
    db.workout_logs.delete_many({"user_email": email})
    db.nutrition_logs.delete_many({"user_email": email})
    db.weight_logs.delete_many({"user_email": email})
    db.prompt_logs.delete_many({"user_email": email})

    return {"message": f"User {email} deleted successfully"}


@router.delete("/{email}/demo-episodes/{episode_id}")
def delete_demo_episode(
    email: str,
    episode_id: str,
    admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
) -> dict:
    """Delete a published demo episode and all of its messages."""
    episode = db.demo_episodes.find_one(
        {"demo_email": email, "episode_id": episode_id},
        {"_id": 0},
    )
    if not episode:
        raise HTTPException(status_code=404, detail="Demo episode not found")

    message_ids = episode.get("published_message_ids", [])
    if message_ids:
        db.demo_messages.delete_many(
            {"demo_email": email, "message_id": {"$in": message_ids}}
        )
        db.message_store.delete_many(
            {"SessionId": email, "demo_message_id": {"$in": message_ids}}
        )

    db.demo_episodes.delete_one({"demo_email": email, "episode_id": episode_id})
    db.demo_prune_log.insert_one(
        {
            "demo_email": email,
            "snapshot_id": episode.get("snapshot_id"),
            "episode_id": episode_id,
            "action": "delete_episode",
            "performed_by": admin.get("email") if admin else None,
            "performed_at": datetime.now(),
        }
    )
    return {"message": "Demo episode deleted successfully"}


@router.delete("/{email}/demo-messages/{message_id}")
def delete_demo_message(
    email: str,
    message_id: str,
    admin: CURRENT_ADMIN_DEP,
    db: MAIN_DB_DEP,
) -> dict:
    """Delete a single published demo message."""
    message = db.demo_messages.find_one(
        {"demo_email": email, "message_id": message_id},
        {"_id": 0},
    )
    if not message:
        raise HTTPException(status_code=404, detail="Demo message not found")

    db.demo_messages.delete_one({"demo_email": email, "message_id": message_id})
    db.message_store.delete_many({"SessionId": email, "demo_message_id": message_id})
    db.demo_episodes.update_one(
        {"demo_email": email, "episode_id": message["episode_id"]},
        {"$pull": {"published_message_ids": message_id}},
    )
    updated_episode = db.demo_episodes.find_one(
        {"demo_email": email, "episode_id": message["episode_id"]},
        {"published_message_ids": 1},
    )
    if updated_episode and not updated_episode.get("published_message_ids"):
        db.demo_episodes.delete_one({"demo_email": email, "episode_id": message["episode_id"]})
    db.demo_prune_log.insert_one(
        {
            "demo_email": email,
            "snapshot_id": message.get("snapshot_id"),
            "episode_id": message["episode_id"],
            "message_id": message_id,
            "action": "delete_message",
            "performed_by": admin.get("email") if admin else None,
            "performed_at": datetime.now(),
        }
    )
    return {"message": "Demo message deleted successfully"}
