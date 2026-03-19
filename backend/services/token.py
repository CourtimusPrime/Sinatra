# services/token.py
from fastapi import HTTPException, Request

from db import queries as q
from services.session import get_user_id_from_request
from services.spotify_auth import get_spotify_oauth


def _resolve_token(user_id: str) -> str:
    """Core token resolution: fetch, refresh if expired, return access token."""
    token_info = q.get_tokens(user_id)
    if not token_info:
        raise HTTPException(status_code=404, detail="User not found in database")

    if not all(token_info.values()):
        raise HTTPException(status_code=400, detail="User token info incomplete")

    sp_oauth = get_spotify_oauth()

    if sp_oauth.is_token_expired(token_info):
        refreshed = sp_oauth.refresh_access_token(token_info["refresh_token"])
        q.upsert_tokens(
            user_id,
            refreshed["access_token"],
            refreshed["refresh_token"],
            refreshed["expires_at"],
        )
        return refreshed["access_token"]

    return token_info["access_token"]


def get_token(request: Request) -> str:
    user_id = get_user_id_from_request(request)
    return _resolve_token(user_id)


def get_token_by_user_id(user_id: str) -> str:
    return _resolve_token(user_id)


def refresh_user_token(user_id: str) -> dict:
    _resolve_token(user_id)
    return {"status": "ok"}
