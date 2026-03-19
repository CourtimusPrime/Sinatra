# db/mongo.py
import os
from functools import lru_cache

from pymongo import MongoClient


@lru_cache
def get_mongo_client():
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise RuntimeError("❌ MONGODB_URI not set.")
    return MongoClient(uri)


@lru_cache
def get_db():
    db_name = os.getenv("MONGODB_DB", "sinatra")
    return get_mongo_client()[db_name]


# Collections (access lazily)
users_collection = get_db().users
playlists_collection = get_db().playlists

# Ensure indexes for last lookups
users_collection.create_index("user_id", unique=True)
