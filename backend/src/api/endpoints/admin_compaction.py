"""
Admin endpoint para compactar histórico de usuários retroativamente.
Requer autenticação de admin.
"""

from fastapi import APIRouter, Depends, HTTPException
from src.services.auth import verify_token
from src.core.deps import get_mongo_database
from src.core.logs import logger
from src.services.history_compactor import HistoryCompactor
from src.services.llm_client import LLMClient


router = APIRouter(prefix="/admin/compaction", tags=["admin"])


@router.post("/compact-user/{user_email}")
async def compact_user_history(
    user_email: str,
    current_user: str = Depends(verify_token),
    db=Depends(get_mongo_database),
):
    """
    Compacta RETROATIVAMENTE o histórico de um usuário.
    Apenas administradores podem usar.
    """

    # Verificar se é admin
    if current_user not in (user_email, "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only the user or an admin can compact their history",
        )

    logger.info(
        "🔄 Starting retroactive compaction for user: %s (requested by: %s)",
        user_email, current_user,
    )

    try:
        # Initialize services
        llm_client = LLMClient.from_config()
        compactor = HistoryCompactor(db, llm_client)

        # Get user profile
        profile = db.get_user_profile(user_email)
        if not profile:
            raise HTTPException(status_code=404, detail=f"User not found: {user_email}")

        # Get ALL messages
        all_messages = db.get_chat_history(user_email, limit=None)
        total_msgs = len(all_messages)
        logger.info("Found %d total messages for user: %s", total_msgs, user_email)

        if total_msgs == 0:
            return {
                "status": "skipped",
                "reason": "No messages to compact",
                "user_email": user_email,
                "total_messages": total_msgs,
            }

        # Run compaction with no active window (process all messages)
        await compactor.compact_history(
            user_email=user_email,
            active_window_size=0,  # Force compaction of all messages
            compaction_threshold=1,  # Lower threshold to force
        )

        # Get updated profile
        updated_profile = db.get_user_profile(user_email)
        summary_len = (
            len(updated_profile.long_term_summary)
            if updated_profile.long_term_summary
            else 0
        )
        summary_preview = (updated_profile.long_term_summary or "EMPTY")[:200]

        logger.info("✅ Retroactive compaction complete for user: %s", user_email)

        return {
            "status": "success",
            "user_email": user_email,
            "total_messages_processed": total_msgs,
            "summary_size_chars": summary_len,
            "summary_preview": summary_preview,
            "message": "History compaction complete.",
        }

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Error during retroactive compaction for user %s: %s",
            user_email, e, exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Error during compaction: {str(e)}"
        ) from e
