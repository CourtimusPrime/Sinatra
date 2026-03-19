# api/system.py
import os
from datetime import UTC, datetime

import requests
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from db.pg import check_connection

router = APIRouter(tags=["system"])


@router.get("/status")
def get_system_status():
    # PostgreSQL check
    pg_status = "online" if check_connection() else "offline"

    # Spotify API check
    try:
        res = requests.get("https://api.spotify.com/v1", timeout=2)
        spotify_status = "online" if res.status_code == 200 else "degraded"
    except Exception:
        spotify_status = "offline"

    # Vercel frontend check
    frontend_url = os.getenv("PRO_FRONTEND_URL", "https://sinatra.live")
    try:
        res = requests.get(frontend_url, timeout=2)
        vercel_status = "online" if res.status_code == 200 else "degraded"
    except Exception:
        vercel_status = "offline"

    return {
        "backend": "online",
        "postgres": pg_status,
        "spotify": spotify_status,
        "vercel_frontend": vercel_status,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/", response_class=PlainTextResponse, include_in_schema=False)
def health_check():
    return "OK"
