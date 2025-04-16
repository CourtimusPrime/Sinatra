# backend/auth/token_handler.py

from fastapi import Query, HTTPException
from backend.db import users_collection
from backend.utils import get_spotify_oauth

sp_oauth = get_spotify_oauth()

def get_token(user_id: str = Query(...)):
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_info = {
        "access_token": user["access_token"],
        "refresh_token": user["refresh_token"],
        "expires_at": user["expires_at"]
    }

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(user["refresh_token"])
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {
                "access_token": refreshed["access_token"],
                "expires_at": refreshed["expires_at"]
            }}
        )
        return refreshed["access_token"]

    return user["access_token"]

def build_token_info(user):
    return {
        "access_token": user["access_token"],
        "refresh_token": user["refresh_token"],
        "expires_at": user["expires_at"]
    }