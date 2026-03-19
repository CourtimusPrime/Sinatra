# api/system.py
import os
from datetime import datetime

import requests
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from pymongo.errors import ConnectionFailure

from db.mongo import get_mongo_client

router = APIRouter(tags=["system"])


@router.get("/status")
def get_system_status():
    client = get_mongo_client()

    # MongoDB check
    try:
        client.admin.command("ping")
        mongo_status = "online"
    except ConnectionFailure:
        mongo_status = "offline"

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
        "mongo": mongo_status,
        "spotify": spotify_status,
        "vercel_frontend": vercel_status,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/", response_class=PlainTextResponse, include_in_schema=False)
def health_check():
    return "OK"
