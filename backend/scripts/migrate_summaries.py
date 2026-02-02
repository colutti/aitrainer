"""
Migration script to convert text-free summaries to JSON-structured summaries.

This script is intended to run ONCE after deploying the new summary system.
It converts all existing long_term_summary fields from text format to JSON format.

Usage:
    python -m scripts.migrate_summaries
"""

import json
import sys
import asyncio
from datetime import datetime

# Add backend to path
sys.path.insert(0, "/home/colutti/projects/personal/backend")

from src.services.database import MongoDatabase
from src.services.llm_client import LLMClient
from src.core.config import settings
from src.core.logs import logger
from mem0 import Memory


def convert_text_summary_to_json(text_summary: str) -> dict:
    """
    Convert text-based summary to JSON structure.

    If text_summary is already JSON, return as-is.
    Otherwise, parse and categorize intelligently.

    Args:
        text_summary: Text summary from old format

    Returns:
        dict: JSON structure with categories
    """
    if not text_summary:
        return {
            "health": [],
            "goals": [],
            "preferences": [],
            "progress": [],
            "restrictions": [],
        }

    # Check if already JSON
    try:
        parsed = json.loads(text_summary)
        if isinstance(parsed, dict) and all(
            cat in parsed for cat in ["health", "goals", "preferences", "progress", "restrictions"]
        ):
            return parsed
    except json.JSONDecodeError:
        pass

    # Convert text to JSON by simple heuristics
    summary_dict = {
        "health": [],
        "goals": [],
        "preferences": [],
        "progress": [],
        "restrictions": [],
    }

    lines = text_summary.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Heuristic categorization
        if any(
            word in line.lower()
            for word in ["lesão", "alergia", "dor", "restrição", "médico", "cirurgia"]
        ):
            summary_dict["health"].append(line)
        elif any(
            word in line.lower()
            for word in ["ganhar", "perder", "objetivo", "meta", "correr"]
        ):
            summary_dict["goals"].append(line)
        elif any(
            word in line.lower()
            for word in ["prefere", "gosta", "horário", "equipamento", "treino"]
        ):
            summary_dict["preferences"].append(line)
        elif any(
            word in line.lower()
            for word in ["agachamento", "supino", "rosca", "kg", "progresso", "→"]
        ):
            summary_dict["progress"].append(line)
        else:
            # Default to health if unclear
            summary_dict["health"].append(line)

    return summary_dict


async def migrate_user_summaries(database: MongoDatabase):
    """
    Migrate all user summaries from text to JSON format.

    Args:
        database: MongoDatabase instance
    """
    logger.info("Starting summary migration...")

    try:
        # Get all users
        all_users = database.db.users.find({})
        users_list = list(all_users)
        total_users = len(users_list)

        logger.info(f"Found {total_users} users to migrate")

        migrated = 0
        skipped = 0
        errors = 0

        for user in users_list:
            email = user.get("email")
            current_summary = user.get("long_term_summary", "")

            try:
                # Skip if already JSON
                try:
                    parsed = json.loads(current_summary)
                    if isinstance(parsed, dict) and "health" in parsed:
                        logger.debug(f"User {email}: Already JSON, skipping")
                        skipped += 1
                        continue
                except json.JSONDecodeError:
                    pass

                # Convert to JSON
                new_summary = convert_text_summary_to_json(current_summary)
                json_str = json.dumps(new_summary, ensure_ascii=False, indent=2)

                # Update in database
                result = database.db.users.update_one(
                    {"email": email},
                    {
                        "$set": {
                            "long_term_summary": json_str,
                            "migration_timestamp": datetime.now().isoformat(),
                        }
                    },
                )

                if result.modified_count > 0:
                    logger.info(f"✅ Migrated user: {email}")
                    migrated += 1
                else:
                    logger.debug(f"User {email}: No changes needed")
                    skipped += 1

            except Exception as e:
                logger.error(f"❌ Error migrating user {email}: {e}")
                errors += 1

        logger.info(f"\nMigration complete:")
        logger.info(f"  ✅ Migrated: {migrated}")
        logger.info(f"  ⏭️  Skipped: {skipped}")
        logger.info(f"  ❌ Errors: {errors}")

    except Exception as e:
        logger.error(f"Fatal error during migration: {e}")
        raise


async def main():
    """Run migration."""
    # Initialize database
    database = MongoDatabase()

    # Run migration
    await migrate_user_summaries(database)

    logger.info("Migration finished.")


if __name__ == "__main__":
    asyncio.run(main())
