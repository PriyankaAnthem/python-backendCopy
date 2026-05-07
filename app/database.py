
import os
from pymongo import MongoClient

_client: MongoClient | None = None

def _get_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI environment variable is not set")
        _client = MongoClient(uri)
    return _client

# Use this in routes: from app.database import db
db = _get_client()[os.getenv("MONGODB_DB", "audioscribe")]