# backend/delete_user.py

from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()  # Load your .env variables

client = MongoClient(os.getenv("MONGODB_URI"))
db = client.spotify_app
users_collection = db.users

target_user = input("user_id: ")

result = users_collection.delete_one({"user_id": target_user})
print(f"Deleted {result.deleted_count} user(s).")
