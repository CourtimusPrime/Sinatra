# backend/auth.py

from fastapi import Query, HTTPException
from backend.db import users_collection
from backend.utils import get_spotify_oauth

sp_oauth = get_spotify_oauth()

def get_token(access_token: str = Query(...)):
    user = users_collection.find_one({"access_token": access_token})
    if not user:
        raise HTTPException(status_code=404, detail="access_token not found in cache! -\(o.o)/-")

    token_info = {
        "access_token": user["access_token"],
        "refresh_token": user["refresh_token"],
        "expires_at": user["expires_at"]
    }

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(user["refresh_token"])
        users_collection.update_one(
            {"access_token": access_token},
            {"$set": {
                "refresh_token": refreshed["refresh_token"],
                "expires_at": refreshed["expires_at"]
            }}
        )
        return refreshed["refresh_token"]

    return user["access_token"]