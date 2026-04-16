"""Firebase Admin initialization module."""

import functools
import json
import os

from firebase_admin import credentials, get_app, initialize_app  # type: ignore

from src.core.config import settings
from src.core.logs import logger


def init_firebase() -> None:
    """
    Initializes the Firebase Admin SDK using credentials from settings.
    """
    firebase_auth_emulator_host = os.getenv("FIREBASE_AUTH_EMULATOR_HOST")

    if firebase_auth_emulator_host and not settings.FIREBASE_CREDENTIALS:
        try:
            initialize_app(
                options={
                    "projectId": os.getenv("FIREBASE_PROJECT_ID", "demo-fityq"),
                }
            )
            logger.info(
                "Firebase Admin initialized with Auth Emulator at %s.",
                firebase_auth_emulator_host,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Failed to initialize Firebase Admin emulator mode: %s", e)
        return

    if not settings.FIREBASE_CREDENTIALS:
        logger.warning(
            "FIREBASE_CREDENTIALS not set. Firebase Admin will not be initialized."
        )
        return

    try:
        # Check if FIREBASE_CREDENTIALS is a JSON string or a file path
        if settings.FIREBASE_CREDENTIALS.strip().startswith("{"):
            cred_dict = json.loads(settings.FIREBASE_CREDENTIALS)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)

        initialize_app(cred)
        logger.info("Firebase Admin initialized successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to initialize Firebase Admin: %s", e)


@functools.lru_cache(maxsize=1)
def ensure_firebase_initialized() -> None:
    """Initializes Firebase Admin once per process, lazily on demand."""
    try:
        get_app()
        return
    except ValueError:
        init_firebase()
