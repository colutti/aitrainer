"""
This module contains the base repository class for all MongoDB repositories.
"""

from pymongo.database import Database
from src.core.logs import logger


class BaseRepository:
    """
    Base repository providing common access to MongoDB collection and logging.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, database: Database, collection_name: str):
        self.collection = database[collection_name]
        self.logger = logger

    def get_paginated_cursor(
        self,
        query: dict,
        page: int = 1,
        page_size: int = 10,
        sort_field: str = "date",
        sort_direction: int = -1,
    ):
        # pylint: disable=too-many-arguments,too-many-positional-arguments
        """Standard pagination logic for MongoDB."""
        total = self.collection.count_documents(query)
        skip = (page - 1) * page_size
        cursor = (
            self.collection.find(query)
            .sort(sort_field, sort_direction)
            .skip(skip)
            .limit(page_size)
        )
        return cursor, total
