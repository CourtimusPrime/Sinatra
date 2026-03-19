# api/auth.py
import base64
import json
import os

import spotipy
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from spotipy.exceptions import SpotifyException

from db.mongo import users_collection
from services.cookie import decode, encode
from services.spotify_auth import get_spotify_oauth
from services.token import refresh_user_token

router = APIRouter(tags=["auth"])

NODE_ENV = os.getenv("NODE_ENV", "development").lower()
IS_DEV = NODE_ENV == "development"

DEV_BASE_URL = os.getenv("DEV_BASE_URL", "http://localhost:5173")
PRO_BASE_URL = os.getenv("PRO_BASE_URL", "https://sinatra.live")
CALLBACK_URL = os.getenv("DEV_CALLBACK") if IS_DEV else os.getenv("PRO_CALLBACK")


def safe_b64decode(data: str):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode()


@router.get("/login")
async def login():
    # Redirect URI for frontend to land on after auth finishes
    frontend_redirect_uri = PRO_BASE_URL + "/home" if not IS_DEV else DEV_BASE_URL + "/home"

    # Encode that into state so /callback knows where to send user
    state_payload = json.dumps({"redirect_uri": frontend_redirect_uri})
    encoded_state = base64.urlsafe_b64encode(state_payload.encode()).decode()

    # Use real, registered backend redirect URI for Spotify
    sp_oauth = get_spotify_oauth(CALLBACK_URL)
    auth_url = sp_oauth.get_authorize_url(state=encoded_state)

    print("🔐 Starting Spotify auth with:")
    print("   CALLBACK_URL =", CALLBACK_URL)
    print("   STATE (decoded) =", state_payload)
    print("   AUTH_URL =", auth_url)

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
        print(f"✅ Extracted redirect_uri from state: {redirect_uri}")
    except Exception as e:
        print(f"❌ Failed to decode state: {e}")
        raise HTTPException(status_code=400, detail=f"State decode error: {e}")

    try:
        sp_oauth = get_spotify_oauth(CALLBACK_URL)
        token_info = sp_oauth.get_access_token(code, as_dict=True)
        sp = spotipy.Spotify(auth=token_info["access_token"])
        profile = sp.current_user()
        user_id = profile.get("id")
    except SpotifyException as e:
        print(f"🙅‍♂️ Token exchange or user fetch failed: {e}")
        if e.http_status == 403:
            raise HTTPException(
                status_code=403,
                detail="Spotify forbids access, the user may not be registered in dashboard",
            )
        raise HTTPException(status_code=500, detail=f"☎️ Internal callback error: {e}")
    except Exception as e:
        print(f"❌ Token exchange or user fetch failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal callback error: {e}")

    if not user_id:
        raise HTTPException(status_code=400, detail="Spotify user ID missing.")

    # Update or create user record
    users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "access_token": token_info["access_token"],
                "refresh_token": token_info["refresh_token"],
                "expires_at": token_info["expires_at"],
            }
        },
        upsert=True,
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

    print(f"🍪 Set sinatra_user_id cookie: {user_id}")
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
        samesite="None",  # Match what you used in login
        secure=True,  # Match what you used in login
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

    print("🔍 /whoami DEBUG:")
    print("🧁  All cookies received:", dict(all_cookies))
    print("🆔  sinatra_user_id cookie:", user_id)

    if not user_id:
        print("🚫 No sinatra_user_id cookie found")
        return JSONResponse(
            {"message": "No sinatra_user_id cookie found"},
            status_code=401,
        )

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        print(f"❌ No user found in DB for user_id: {user_id}")
        return JSONResponse(
            {"message": f"User ID from cookie: {user_id} not found in DB"},
            status_code=404,
        )

    print(f"✅ User found: {user.get('display_name')} ({user_id})")

    return {
        "message": "User identified via cookie",
        "user_id": user_id,
        "display_name": user.get("display_name"),
        "profile_image_url": user.get("profile_image_url"),
    }
