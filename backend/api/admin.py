# api/admin.py
from datetime import UTC, datetime

import spotipy
from fastapi import APIRouter, Query

from db.mongo import playlists_collection, users_collection
from services.spotify import get_spotify_client

router = APIRouter(tags=["admin"])


@router.post("/admin/backfill-playlist-metadata")
def backfill_playlist_metadata():
    users = users_collection.find({"playlists.all": {"$exists": True}})
    updated = 0

    for user in users:
        access_token = user.get("access_token")
        if not access_token:
            continue

        sp = spotipy.Spotify(auth=access_token)
        updated_playlists = []

        for pl in user.get("playlists.all", []):
            try:
                playlist = sp.playlist(pl["playlist_id"])
                pl["track_count"] = playlist["tracks"]["total"]
                pl["external_url"] = playlist["external_urls"]["spotify"]
                updated_playlists.append(pl)
            except Exception as e:
                print(f"⚠️ Failed to update playlist {pl['playlist_id']}: {e}")
                continue

        users_collection.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"playlists.all": updated_playlists}},
        )
        updated += 1

    return {"status": "ok", "users_updated": updated}


@router.post("/admin/sync_playlists")
def sync_playlists(user_id: str = Query(...)):
    sp = get_spotify_client(user_id)

    all_playlists = []
    offset = 0
    limit = 50
    total_fetched = 0

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
                    "owner_id": p["owner"]["id"],
                    "image": p["images"][0]["url"] if p["images"] else None,
                    "external_url": p["external_urls"]["spotify"],
                }
            )

        offset += limit
        total_fetched += len(items)

    playlists_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "user_id": user_id,
                "playlists": all_playlists,
                "last_updated": datetime.now(UTC),
            }
        },
        upsert=True,
    )

    return {
        "status": "ok",
        "user_id": user_id,
        "total_playlists_fetched": total_fetched,
        "total_playlists_saved": len(all_playlists),
    }
