# backend/routes/platform.py

from fastapi import APIRouter, HTTPException
from backend.utils.platform_auth import generate_pkce_pair, build_auth_url
import os

router = APIRouter()

PLATFORM_CONFIGS = {
    "spotify": {
        "client_id": os.getenv("SPOTIFY_CLIENT_ID"),
        "redirect_uri": os.getenv("SPOTIFY_REDIRECT_URI"),
        "auth_url": "https://accounts.spotify.com/authorize",
        "scopes": ["user-read-email", "playlist-read-private"]
    },
    "tidal": {
        "client_id": os.getenv("TIDAL_ID"),
        "redirect_uri": os.getenv("TIDAL_REDIRECT_URI"),
        "auth_url": "https://login.tidal.com/authorize",
        "scopes": [
            "user.read", "collection.read", "search.read",
            "playlists.read", "playlists.write", "collection.write",
            "playback", "recommendations.read", "entitlements.read"
        ]
    }
}

@router.get("/auth-url/{platform}")
def get_auth_url(platform: str):
    config = PLATFORM_CONFIGS.get(platform)
    if not config:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    code_verifier, code_challenge = generate_pkce_pair()
    url = build_auth_url(
        base_url=config["auth_url"],
        client_id=config["client_id"],
        redirect_uri=config["redirect_uri"],
        code_challenge=code_challenge,
        scopes=config["scopes"]
    )
    return {"auth_url": url, "code_verifier": code_verifier}