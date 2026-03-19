# api/admin.py
import os

import spotipy
from fastapi import APIRouter, Header, HTTPException, Query

from db import queries as q
from services.spotify import get_spotify_client

router = APIRouter(tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


def _verify_admin(x_admin_secret: str = Header(None)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/admin/backfill-playlist-metadata")
def backfill_playlist_metadata(x_admin_secret: str = Header(None)):
    _verify_admin(x_admin_secret)
    users = q.get_all_users_with_tokens()
    updated = 0

    for user in users:
        sp = spotipy.Spotify(auth=user["access_token"])
        saved = q.get_saved_playlists(user["spotify_id"])
        enriched = []

        for pl in saved:
            try:
                playlist = sp.playlist(pl["id"])
                enriched.append(
                    {
                        "id": pl["id"],
                        "tracks": playlist["tracks"]["total"],
                        "external_url": playlist["external_urls"]["spotify"],
                    }
                )
            except Exception:
                continue

        if enriched:
            q.backfill_playlist_metadata(user["spotify_id"], enriched)
            updated += 1

    return {"status": "ok", "users_updated": updated}


@router.post("/admin/sync_playlists")
def sync_playlists(user_id: str = Query(...), x_admin_secret: str = Header(None)):
    _verify_admin(x_admin_secret)
    sp = get_spotify_client(user_id)

    all_playlists = []
    offset = 0
    limit = 50

    user_profile = sp.current_user()
    spotify_user_id = user_profile["id"]

    while True:
        page = sp.current_user_playlists(limit=limit, offset=offset)
        items = page.get("items", [])

        if not items:
            break

        for p in items:
            if p["owner"]["id"] != spotify_user_id or p["tracks"]["total"] < 4:
                continue

            all_playlists.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "tracks": p["tracks"]["total"],
                    "image": p["images"][0]["url"] if p["images"] else None,
                    "external_url": p["external_urls"]["spotify"],
                }
            )

        offset += limit

    saved = q.sync_user_playlists(user_id, all_playlists)

    return {
        "status": "ok",
        "user_id": user_id,
        "total_playlists_saved": saved,
    }
