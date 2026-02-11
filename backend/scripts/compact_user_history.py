#!/usr/bin/env python3
"""
Script para compactar RETROATIVAMENTE o histórico de um usuário.
Processa TODAS as mensagens do usuário e gera um long_term_summary.

Uso:
    python scripts/compact_user_history.py rafacolucci@gmail.com
"""

import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, '/home/colutti/projects/personal/backend')

# Load .env.prod BEFORE importing settings
from dotenv import load_dotenv
env_file = Path('/home/colutti/projects/personal/backend/.env.prod')
if env_file.exists():
    load_dotenv(env_file)
    print(f"✅ Loaded environment from {env_file}")
else:
    print(f"⚠️  .env.prod not found at {env_file}")

from src.services.database import MongoDatabase  # noqa: E402
from src.services.history_compactor import HistoryCompactor  # noqa: E402
from src.core.logs import logger  # noqa: E402
from src.services.llm_client import LLMClient  # noqa: E402


async def compact_user_retroactively(user_email: str):
    """Compacta TODAS as mensagens do usuário retroativamente."""

    logger.info("🔄 Starting retroactive compaction for user: %s", user_email)

    try:
        # Initialize dependencies
        db = MongoDatabase()
        llm_client = LLMClient.from_config()
        compactor = HistoryCompactor(db, llm_client)

        # Get user profile
        profile = db.get_user_profile(user_email)
        if not profile:
            logger.error("User not found: %s", user_email)
            return False

        # Get ALL messages
        all_messages = db.get_chat_history(user_email, limit=1000)  # Large limit instead of None
        total_msgs = len(all_messages)
        logger.info("Found %d total messages for user: %s", total_msgs, user_email)

        if total_msgs == 0:
            logger.warning("No messages to compact for user: %s", user_email)
            return False

        # Run compaction with increased window to process MORE messages
        # Set active_window_size to 0 to force compaction of ALL messages
        await compactor.compact_history(
            user_email=user_email,
            active_window_size=0,  # Force compaction of all messages
            compaction_threshold=1,  # Lower threshold to force
        )

        # Get updated profile
        updated_profile = db.get_user_profile(user_email)
        summary_len = 0
        summary_preview = "EMPTY"
        
        if updated_profile and updated_profile.long_term_summary:
            summary_len = len(updated_profile.long_term_summary)
            summary_preview = updated_profile.long_term_summary[:200]

        logger.info("✅ Retroactive compaction complete!")
        logger.info("   Total messages processed: %d", total_msgs)
        logger.info("   Summary size: %d chars", summary_len)
        logger.info("   Summary preview: %s", summary_preview)

        return True

    except Exception as e:
        logger.error("Error during retroactive compaction: %s", e, exc_info=True)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python compact_user_history.py <email>")
        print("Example: python compact_user_history.py rafacolucci@gmail.com")
        sys.exit(1)

    user_email = sys.argv[1]
    success = asyncio.run(compact_user_retroactively(user_email))
    sys.exit(0 if success else 1)
