"""
This module contains the base repository class for all MongoDB repositories.
"""

from pymongo.database import Database
from bson import ObjectId
from src.core.logs import logger


class BaseRepository:
    """
    Base repository providing common access to MongoDB collection and logging.
    """

    def __init__(self, database: Database, collection_name: str):
        self.collection = database[collection_name]
        self.logger = logger

    def get_paginated_cursor(
        self,
        query: dict,
        page: int = 1,
        page_size: int = 10,
        sort: tuple[str, int] | None = None,
    ):
        """Standard pagination logic for MongoDB."""
        if sort is None:
            sort = ("date", -1)

        total = self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort(sort[0], sort[1])
            .skip(skip)
            .limit(page_size)
        )
        return cursor, total

    def upsert_document(
        self, query: dict, data: dict, log_name: str
    ) -> tuple[str, bool]:
        """Upserts a document and returns its ID and whether it was newly created."""
        result = self.collection.update_one(query, {"$set": data}, upsert=True)
        is_new = result.upserted_id is not None

        if is_new:
            doc_id = str(result.upserted_id)
            self.logger.info("Created new %s for %s", log_name, query)
        else:
            existing = self.collection.find_one(query)
            doc_id = str(existing["_id"]) if existing else ""
            self.logger.info("Updated existing %s for %s", log_name, query)

        return doc_id, is_new

    def replace_user_owned_document(
        self,
        document_id: str,
        user_email: str,
        data: dict,
        log_name: str,
    ) -> bool:
        """Replace a user-owned document and emit consistent logging."""
        result = self.collection.replace_one(
            {"_id": ObjectId(document_id), "user_email": user_email},
            data,
        )
        updated = result.matched_count > 0
        if updated:
            self.logger.info("%s %s updated for user %s", log_name, document_id, user_email)
        else:
            self.logger.warning("%s %s not found for update", log_name, document_id)
        return updated

    def replace_user_owned_log(
        self,
        document_id: str,
        user_email: str,
        data: dict,
        log_name: str,
    ) -> bool:
        """Attach the owner and replace a user-owned log document."""
        payload = dict(data)
        payload["user_email"] = user_email
        return self.replace_user_owned_document(
            document_id=document_id,
            user_email=user_email,
            data=payload,
            log_name=log_name,
        )
