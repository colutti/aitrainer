"""Firebase Admin initialization module."""

import functools
import json
import os
from typing import Any

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
            cred_dict = _load_service_account_json(settings.FIREBASE_CREDENTIALS)
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS)

        initialize_app(cred)
        logger.info("Firebase Admin initialized successfully.")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to initialize Firebase Admin: %s", e)


def _load_service_account_json(raw_credentials: str) -> dict[str, Any]:
    """
    Load service account JSON from an env var.

    Cloud Run env vars can preserve literal newlines inside the private_key field,
    which makes the raw JSON invalid. Normalize that case before parsing.
    """
    try:
        return json.loads(raw_credentials)
    except json.JSONDecodeError as first_error:
        if '"private_key"' not in raw_credentials:
            raise first_error

        key_marker = '"private_key":"'
        key_start = raw_credentials.find(key_marker)
        if key_start == -1:
            raise first_error
        key_start += len(key_marker)

        key_end = raw_credentials.find('","client_email"', key_start)
        if key_end == -1:
            raise first_error

        private_key = raw_credentials[key_start:key_end].replace("\r\n", "\n")
        normalized = (
            raw_credentials[:key_start]
            + private_key.replace("\n", "\\n")
            + raw_credentials[key_end:]
        )
        return json.loads(normalized)


@functools.lru_cache(maxsize=1)
def ensure_firebase_initialized() -> None:
    """Initializes Firebase Admin once per process, lazily on demand."""
    try:
        get_app()
        return
    except ValueError:
        init_firebase()
