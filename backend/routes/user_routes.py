# backend/routes/user-routes.py

from fastapi import APIRouter, HTTPException, Query, Depends
from backend.db import users_collection
from backend.auth import get_token
import spotipy

router = APIRouter()

@router.get("/me", tags=["User"], summary="Gets info on the user")
def get_current_user(access_token: str = Depends(get_token), user_id: str = Query(...)):
    sp = spotipy.Spotify(auth=access_token)
    user = sp.current_user()
    mongo_user = users_collection.find_one({"user_id": user["id"]})

    return {
    "user_id": user["id"],
    "display_name": user["display_name"],
    "email": user["email"],
    "profile_picture": user["images"][0]["url"] if user.get("images") else None,
    "featured_playlists": mongo_user.get("featured_playlists", []) if mongo_user else []
}

@router.get("/users", tags=["User"], summary="Get list of all users")
def get_users():
    return list(users_collection.find({}, {"_id": 0, "user_id": 1, "display_name": 1, "email": 1}))

@router.get("/user-playlists", tags=["User"], summary="Get the user's playlists")
def get_user_playlists(user_id: str = Query(...)):
    user = users_collection.find_one({"user_id": user_id})
    if not user or "important_playlists" not in user:
        return []

    public = []
    for pid in user["important_playlists"]:
        match = users_collection.find_one(
            {"public_playlists.playlist_id": pid},
            {"public_playlists.$": 1}
        )
        if match and "public_playlists" in match:
            public.append(match["public_playlists"][0])
    return public

@router.get("/public-playlist/{playlist_id}", tags=["User"], summary="Gets details on a playlist")
def get_public_playlist(playlist_id: str):
    match = users_collection.find_one(
        {"public_playlists.playlist_id": playlist_id},
        {"public_playlists.$": 1}
    )
    if not match or "public_playlists" not in match:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return match["public_playlists"][0]

@router.post("/complete-onboarding", tags=["User"], summary="Push data to mongodb")
def complete_onboarding(data: dict):
    if not all(k in data for k in ["user_id", "display_name", "profile_picture", "playlist_ids"]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    access_token = get_token(data["user_id"])
    sp = spotipy.Spotify(auth=access_token)
    full_playlists = []

    for pid in data["playlist_ids"]:
        playlist = sp.playlist(pid)
        tracks = []
        for item in playlist["tracks"]["items"]:
            track = item["track"]
            if track is None:
                continue
            tracks.append({
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"],
                "album_art": track["album"]["images"][0]["url"] if track["album"]["images"] else None,
                "isrc": track.get("external_ids", {}).get("isrc"),
                "track_id": track["id"]
            })

        full_playlists.append({
            "playlist_id": pid,
            "name": playlist["name"],
            "image": playlist["images"][0]["url"] if playlist["images"] else None,
            "tracks": tracks
        })

    users_collection.update_one(
        {"user_id": data["user_id"]},
        {"$set": {
            "display_name": data["display_name"],
            "profile_picture": data["profile_picture"],
            "important_playlists": data["playlist_ids"],
            "featured_playlists": data.get("featured_playlists", []),
            "onboarded": True
        }}
    )

    for pl in full_playlists:
        users_collection.update_one(
            {"user_id": data["user_id"]},
            {"$addToSet": {"public_playlists": pl}},
            upsert=True
        )

    return {"status": "ok"}

@router.get("/has-completed-onboarding", tags=["User"], summary="Check if user completed onboarding")
def has_completed_onboarding(user_id: str = Query(...)):
    user = users_collection.find_one({"user_id": user_id}, {"_id": 0, "onboarded": 1})
    return {"completed": user.get("onboarded", False) if user else False}