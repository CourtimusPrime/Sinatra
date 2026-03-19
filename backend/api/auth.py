# api/auth.py
import base64
import json
import logging
import os

import spotipy
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from spotipy.exceptions import SpotifyException

from db import queries as q
from services.cookie import decode, encode
from services.spotify_auth import get_spotify_oauth
from services.token import refresh_user_token

router = APIRouter(tags=["auth"])

logger = logging.getLogger(__name__)

NODE_ENV = os.getenv("NODE_ENV", "development").lower()
IS_DEV = NODE_ENV == "development"

DEV_BASE_URL = os.getenv("DEV_BASE_URL", "http://localhost:5173")
PRO_BASE_URL = os.getenv("PRO_BASE_URL", "https://sinatra.live")
CALLBACK_URL = os.getenv("DEV_CALLBACK") if IS_DEV else os.getenv("PRO_CALLBACK")

ALLOWED_REDIRECT_ORIGINS = {DEV_BASE_URL, PRO_BASE_URL}


def safe_b64decode(data: str):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode()


@router.get("/login")
async def login():
    frontend_redirect_uri = PRO_BASE_URL + "/home" if not IS_DEV else DEV_BASE_URL + "/home"

    state_payload = json.dumps({"redirect_uri": frontend_redirect_uri})
    encoded_state = base64.urlsafe_b64encode(state_payload.encode()).decode()

    sp_oauth = get_spotify_oauth(CALLBACK_URL)
    auth_url = sp_oauth.get_authorize_url(state=encoded_state)

    logger.debug("Starting Spotify auth flow")
    return RedirectResponse(auth_url)


@router.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    try:
        decoded_state = safe_b64decode(state)
        redirect_uri = json.loads(decoded_state)["redirect_uri"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    if not any(redirect_uri.startswith(origin) for origin in ALLOWED_REDIRECT_ORIGINS):
        raise HTTPException(status_code=400, detail="Invalid redirect URI")

    try:
        sp_oauth = get_spotify_oauth(CALLBACK_URL)
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        sp = spotipy.Spotify(auth=token_info["access_token"])
        profile = sp.current_user()
        user_id = profile.get("id")
    except SpotifyException as e:
        logger.warning("Token exchange or user fetch failed: %s", e)
        if e.http_status == 403:
            raise HTTPException(
                status_code=403,
                detail="Spotify forbids access, the user may not be registered in dashboard",
            )
        raise HTTPException(status_code=500, detail="Authentication failed")
    except Exception as e:
        logger.error("Unexpected callback error: %s", e)
        raise HTTPException(status_code=500, detail="Authentication failed")

    if not user_id:
        raise HTTPException(status_code=400, detail="Spotify user ID missing.")

    # Upsert user profile (needed before tokens due to FK)
    display_name = profile.get("display_name") or user_id
    profile_image = profile["images"][0]["url"] if profile.get("images") else None
    q.upsert_user(user_id, display_name, profile_image)

    # Store tokens
    q.upsert_tokens(
        user_id,
        token_info["access_token"],
        token_info["refresh_token"],
        token_info["expires_at"],
    )

    # Build redirect response with secure, server-set cookie
    frontend_base = DEV_BASE_URL if IS_DEV else PRO_BASE_URL
    redirect_url = f"{frontend_base}/home"
    response = RedirectResponse(url=redirect_url)

    response.set_cookie(
        key="sinatra_user_id",
        value=encode(user_id),
        httponly=True,
        secure=not IS_DEV,
        samesite="None" if not IS_DEV else "Lax",
        path="/",
        max_age=3600 * 24 * 7,
    )

    logger.debug("Set sinatra_user_id cookie for user %s", user_id)
    return response


@router.get("/refresh_token")
def refresh_token(refresh_token: str = Query(...)):
    sp_oauth = get_spotify_oauth()
    refreshed = sp_oauth.refresh_access_token(refresh_token)
    return {
        "access_token": refreshed["access_token"],
        "expires_in": refreshed["expires_in"],
    }


@router.get("/refresh-session")
def refresh_session(user_id: str = Query(...)):
    return refresh_user_token(user_id)


@router.get("/logout")
def logout_user():
    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(
        key="sinatra_user_id",
        path="/",
        samesite="None" if not IS_DEV else "Lax",
        secure=not IS_DEV,
    )
    return response


@router.get("/whoami")
def whoami(request: Request):
    all_cookies = request.cookies
    cookie_val = all_cookies.get("sinatra_user_id")
    user_id = None
    if cookie_val:
        try:
            user_id = decode(cookie_val)
        except Exception:
            user_id = None

    if not user_id:
        return JSONResponse(
            {"message": "No sinatra_user_id cookie found"},
            status_code=401,
        )

    user = q.get_user(user_id)
    if not user:
        return JSONResponse(
            {"message": "User not found"},
            status_code=404,
        )

    return {
        "message": "User identified via cookie",
        "user_id": user_id,
        "display_name": user.get("display_name"),
        "profile_image_url": user.get("profile_image_url"),
    }
