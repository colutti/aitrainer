"""Dependency injection and database connections for the admin service."""
# pylint: disable=invalid-name
from typing import Annotated, Any, TypeAlias
import os
from pymongo import MongoClient
from pymongo.database import Database
from fastapi import Request, Depends

# Database connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client: MongoClient = MongoClient(mongo_uri)

def get_admin_db() -> Database[Any]:
    """Return the MongoDB database for admin-specific data."""
    return client[os.getenv("DB_NAME", "aitrainer_admin")]

def get_main_db() -> Database[Any]:
    """Return the main MongoDB database used by the core application."""
    return client[os.getenv("MAIN_DB_NAME", "aitrainerdb")]

ADMIN_DB_DEP: TypeAlias = Annotated[Database[Any], Depends(get_admin_db)]
MAIN_DB_DEP: TypeAlias = Annotated[Database[Any], Depends(get_main_db)]

def get_current_admin(request: Request) -> dict[str, Any] | None:
    """Dependency to retrieve the currently authenticated admin user from the request state."""
    return getattr(request.state, "user", None)

CURRENT_ADMIN_DEP: TypeAlias = Annotated[
    dict[str, Any] | None, Depends(get_current_admin)
]
