"""
Firebase Admin initialization module.
"""

import json
from firebase_admin import credentials, initialize_app
from src.core.config import settings
from src.core.logs import logger

def init_firebase() -> None:
    """
    Initializes the Firebase Admin SDK using credentials from settings.
    """
    if not settings.FIREBASE_CREDENTIALS:
        logger.warning("FIREBASE_CREDENTIALS not set. Firebase Admin will not be initialized.")
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
    except Exception as e:
        logger.error("Failed to initialize Firebase Admin: %s", e)
