from pymongo.database import Database
from src.core.logs import logger

class BaseRepository:
    def __init__(self, database: Database, collection_name: str):
        self.collection = database[collection_name]
        self.logger = logger
