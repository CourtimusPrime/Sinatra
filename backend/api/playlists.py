# api/playlists.py

import spotipy
from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request

from db.mongo import playlists_collection, users_collection
from models.playlists import (
    FeaturedPlaylistsUpdateRequest,
)
from services.cookie import get_user_id_from_request
from services.token import get_token

router = APIRouter(tags=["playlists"])


@router.get("/playlists")
def get_playlists(
    user_id: str = Query(...),
    limit: int = Query(50, ge=1, le=50),
    offset: int = Query(0, ge=0),
):
    access_token = get_token(user_id)
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
    user = users_collection.find_one({"user_id": user_id}, {"playlists.all": 1})
    if not user or "playlists.all" not in user:
        return []

    return user["playlists.all"]


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
        except Exception as e:
            print(f"⚠️ Failed to fetch metadata for playlist {pl['id']}: {e}")

    if not enriched:
        raise HTTPException(status_code=400, detail="No valid playlists to add")

    result = users_collection.update_one(
        {"user_id": user_id},
        {"$addToSet": {"playlists.all": {"$each": enriched}}},
        upsert=True,
    )

    return {"status": "added", "modified_count": result.modified_count}


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
    print(f"🗑️ Deleting playlists {playlist_ids} for user {user_id}")

    result = users_collection.update_one(
        {"user_id": user_id},
        {"$pull": {"playlists.all": {"id": {"$in": playlist_ids}}}},
    )

    return {"status": "deleted", "deleted_count": result.modified_count}


@router.post("/update-featured")
def update_featured_playlists(data: FeaturedPlaylistsUpdateRequest = Body(...)):
    user_id = data.user_id
    playlist_ids = data.playlist_ids

    print(f"🔄 Incoming update-featured request for user: {user_id}")
    print(f"📦 Playlist IDs received: {playlist_ids}")

    if not user_id or not isinstance(playlist_ids, list):
        raise HTTPException(status_code=400, detail="Invalid input")

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_playlists = user.get("playlists", {}).get("all", [])
    known_ids = {pl.get("id") for pl in all_playlists}

    normalized_ids = [pid for pid in playlist_ids if pid in known_ids]

    users_collection.update_one(
        {"user_id": user_id}, {"$set": {"playlists.featured": normalized_ids}}
    )

    return {"status": "ok", "count": len(normalized_ids)}


@router.get("/playlist-info")
def get_playlist_info(user_id: str = Query(...), playlist_id: str = Query(...)):
    access_token = get_token(user_id)
    sp = spotipy.Spotify(auth=access_token)
    playlist = sp.playlist(playlist_id)

    return {
        "name": playlist["name"],
        "image": playlist["images"][0]["url"] if playlist["images"] else None,
    }


@router.get("/user-playlists")
def get_user_playlists(user_id: str = Query(...)):
    doc = playlists_collection.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="No synced playlists found for user.")

    return {
        "user_id": doc["user_id"],
        "last_updated": doc.get("last_updated"),
        "playlists": doc.get("playlists", []),
    }


@router.get("/synced-playlists/paginated")
def get_paginated_playlists(user_id: str = Query(...), offset: int = 0, limit: int = 50):
    doc = playlists_collection.find_one({"user_id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="No synced playlists found.")

    all_playlists = doc.get("playlists", [])
    total = len(all_playlists)
    sliced = all_playlists[offset : offset + limit]

    return {"total": total, "playlists": sliced}
