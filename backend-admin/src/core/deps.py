"""Dependency injection and database connections for the admin service."""
from typing import Annotated
import os
import pymongo
from fastapi import Request, Depends

# Database connection
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = pymongo.MongoClient(mongo_uri)

def get_admin_db():
    """Return the MongoDB database for admin-specific data."""
    return client[os.getenv("DB_NAME", "aitrainer_admin")]

def get_main_db():
    """Return the main MongoDB database used by the core application."""
    return client[os.getenv("MAIN_DB_NAME", "aitrainerdb")]

AdminDB = Annotated[pymongo.database.Database, Depends(get_admin_db)]
MainDB = Annotated[pymongo.database.Database, Depends(get_main_db)]

def get_current_admin(request: Request):
    """Dependency to retrieve the currently authenticated admin user from the request state."""
    return getattr(request.state, "user", None)

CurrentAdmin = Annotated[dict, Depends(get_current_admin)]
