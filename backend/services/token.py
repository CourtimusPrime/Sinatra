# services/token.py
from fastapi import HTTPException, Request

from db.mongo import users_collection
from services.cookie import get_user_id_from_request
from services.spotify_auth import get_spotify_oauth


def get_token(request: Request) -> str:
    user_id = get_user_id_from_request(request)

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found in database")

    token_info = {
        "access_token": user.get("access_token"),
        "refresh_token": user.get("refresh_token"),
        "expires_at": user.get("expires_at"),
    }

    if not all(token_info.values()):
        raise HTTPException(status_code=400, detail="User token info incomplete")

    sp_oauth = get_spotify_oauth()

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(user["refresh_token"])
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "access_token": refreshed["access_token"],
                    "refresh_token": refreshed["refresh_token"],
                    "expires_at": refreshed["expires_at"],
                }
            },
        )
        return refreshed["access_token"]

    return token_info["access_token"]


def refresh_user_token(user_id: str) -> dict:
    _ = get_token(user_id)
    return {"status": "ok"}


def get_token_by_user_id(user_id: str) -> str:
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    token_info = {
        "access_token": user.get("access_token"),
        "refresh_token": user.get("refresh_token"),
        "expires_at": user.get("expires_at"),
    }

    if not all(token_info.values()):
        raise HTTPException(status_code=400, detail="Token info incomplete")

    sp_oauth = get_spotify_oauth()

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(user["refresh_token"])
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "access_token": refreshed["access_token"],
                    "refresh_token": refreshed["refresh_token"],
                    "expires_at": refreshed["expires_at"],
                }
            },
        )
        return refreshed["access_token"]

    return token_info["access_token"]
