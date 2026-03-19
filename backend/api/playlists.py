# api/playlists.py
import logging

import spotipy
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from db import queries as q
from models.playlists import FeaturedPlaylistsUpdateRequest
from services.session import get_user_id_from_request
from services.token import get_token, get_token_by_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["playlists"])


@router.get("/playlists")
def get_playlists(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    access_token = get_token_by_user_id(user_id)
    sp = spotipy.Spotify(auth=access_token)
    raw = sp.current_user_playlists(limit=limit, offset=offset)

    playlists = [
        {
            "id": p["id"],
            "name": p["name"],
            "owner": p["owner"]["id"],
            "tracks": p["tracks"]["total"],
            "image": p["images"][0]["url"] if p["images"] else None,
        }
        for p in raw["items"]
    ]

    return {"items": playlists}


@router.get("/all-playlists")
def get_all_user_playlists(user_id: str = Query(...)):
    playlists = q.get_saved_playlists(user_id)
    return playlists


@router.post("/add-playlists")
async def add_playlists(
    request: Request,
    access_token: str = Depends(get_token),
):
    user_id = get_user_id_from_request(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    playlists = body.get("playlists", [])
    if not isinstance(playlists, list) or not all("id" in p for p in playlists):
        raise HTTPException(status_code=400, detail="Invalid playlist data")

    sp = spotipy.Spotify(auth=access_token)
    enriched = []

    for pl in playlists:
        try:
            playlist = sp.playlist(pl["id"])
            enriched.append(
                {
                    "id": pl["id"],
                    "name": playlist["name"],
                    "image": (playlist["images"][0]["url"] if playlist["images"] else None),
                    "tracks": playlist["tracks"]["total"],
                    "external_url": playlist["external_urls"]["spotify"],
                }
            )
        except Exception:
            logger.warning("Failed to fetch metadata for playlist %s", pl["id"])

    if not enriched:
        raise HTTPException(status_code=400, detail="No valid playlists to add")

    count = q.add_saved_playlists(user_id, enriched)
    return {"status": "added", "modified_count": count}


@router.post("/delete-playlists")
async def delete_playlists(
    request: Request,
    access_token: str = Depends(get_token),
):
    user_id = get_user_id_from_request(request)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    playlists = body.get("playlists", [])
    if not isinstance(playlists, list) or not all("id" in p for p in playlists):
        raise HTTPException(status_code=400, detail="Invalid playlist data")

    playlist_ids = [p["id"] for p in playlists]
    count = q.remove_saved_playlists(user_id, playlist_ids)
    return {"status": "deleted", "deleted_count": count}


@router.post("/update-featured")
def update_featured_playlists(data: FeaturedPlaylistsUpdateRequest = Body(...)):
    user_id = data.user_id
    playlist_ids = data.playlist_ids

    if not user_id or not isinstance(playlist_ids, list):
        raise HTTPException(status_code=400, detail="Invalid input")

    user = q.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    count = q.update_featured_playlists(user_id, playlist_ids)
    return {"status": "ok", "count": count}


@router.get("/playlist-info")
def get_playlist_info(user_id: str = Query(...), playlist_id: str = Query(...)):
    access_token = get_token_by_user_id(user_id)
    sp = spotipy.Spotify(auth=access_token)
    playlist = sp.playlist(playlist_id)

    return {
        "name": playlist["name"],
        "image": playlist["images"][0]["url"] if playlist["images"] else None,
    }


@router.get("/user-playlists")
def get_user_playlists(user_id: str = Query(...)):
    playlists = q.get_synced_playlists(user_id)
    if not playlists:
        raise HTTPException(status_code=404, detail="No synced playlists found for user.")

    return {
        "user_id": user_id,
        "playlists": playlists,
    }


@router.get("/synced-playlists/paginated")
def get_paginated_playlists(user_id: str = Query(...), offset: int = 0, limit: int = 50):
    all_playlists = q.get_synced_playlists(user_id)
    if not all_playlists:
        raise HTTPException(status_code=404, detail="No synced playlists found.")

    total = len(all_playlists)
    sliced = all_playlists[offset : offset + limit]

    return {"total": total, "playlists": sliced}
