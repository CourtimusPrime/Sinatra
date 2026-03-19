# api/public.py
import spotipy
from fastapi import APIRouter, HTTPException, Query

from db.mongo import users_collection
from services.spotify import build_track_data
from services.token import get_token_by_user_id

router = APIRouter(tags=["public"])


def _build_profile_response(user_id: str):
    """Return the public profile document for the given user."""
    projection = {
        "user_id": 1,
        "display_name": 1,
        "profile_image_url": 1,
        "profile_picture": 1,
        "playlists": 1,
        "genre_analysis": 1,
        "genres_analysis": 1,
        "genres": 1,
        "last_played_track": 1,
    }
    doc = users_collection.find_one({"user_id": user_id}, projection)
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")

    playlists_data = doc.get("playlists", {})
    all_playlists = playlists_data.get("all", [])
    featured_ids = playlists_data.get("featured", [])

    playlist_lookup = {pl.get("id") or pl.get("playlist_id"): pl for pl in all_playlists}
    featured_playlists = [
        playlist_lookup.get(pid) for pid in featured_ids if pid in playlist_lookup
    ]

    genres_data = doc.get("genre_analysis") or doc.get("genres_analysis") or doc.get("genres")
    last_played = doc.get("last_played_track", {})

    return {
        "user_id": doc.get("user_id"),
        "display_name": doc.get("display_name"),
        "profile_picture": doc.get("profile_image_url") or doc.get("profile_picture"),
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played,
    }


@router.get("/public-profile/{user_id}")
def get_public_profile(user_id: str):
    """Fetch a user's public profile via path parameter."""
    return _build_profile_response(user_id)


@router.get("/public-profile")
def get_public_profile_query(user_id: str = Query(...)):
    """Fetch a user's public profile via query parameter."""
    return _build_profile_response(user_id)


@router.get("/public-track/{user_id}")
def get_public_track(user_id: str):
    doc = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")

    track = doc.get("last_played_track")
    if not track:
        # Gracefully indicate missing track rather than returning 404
        return {"track": None}

    required_keys = {"id", "name", "artist", "album", "album_art_url"}
    if not isinstance(track, dict) or not required_keys.issubset(track.keys()):
        raise HTTPException(status_code=422, detail="Track data is malformed")

    return {"track": track}


@router.get("/public-genres/{user_id}")
def get_public_genres(user_id: str):
    doc = users_collection.find_one({"user_id": user_id})
    if not doc or "genre_analysis" not in doc:
        raise HTTPException(status_code=404, detail="No genre data found")
    return doc["genre_analysis"]


@router.get("/public-played/{user_id}")
def get_public_recently_played(user_id: str, limit: int = 1):
    """Fetch and render a user's most recently played track from a public visitor"""
    try:
        access_token = get_token_by_user_id(user_id)
        sp = spotipy.Spotify(auth=access_token)

        recent = sp.current_user_recently_played(limit=limit)
        if not recent["items"]:
            return {"track": None}

        track = recent["items"][0]["track"]
        track_data = build_track_data(track, sp)

        existing = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
        if existing and existing.get("last_played_track", {}).get("id") == track_data["id"]:
            print("🟡 Track already stored, skipping update.")
            return {"status": "unchanged", "track": track_data}

        users_collection.update_one(
            {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
        )

        return {"track": track_data}
    except Exception as e:
        print(f"⚠️ Public recently played error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recently played track")


@router.post("/public-update-playing/{user_id}")
def public_update_playing(user_id: str):
    """Update a user's recently_played_track on mongo from public"""
    try:
        access_token = get_token_by_user_id(user_id)
        sp = spotipy.Spotify(auth=access_token)

        current = sp.current_playback()
        if not current or not current.get("item"):
            raise HTTPException(status_code=404, detail="nothing is currently playing")

        track_data = build_track_data(current["item"], sp)

        existing = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
        if existing and existing.get("last_played_track", {}).get("id") == track_data["id"]:
            print("🟡 Track already stored, skipping update.")
            return {"status": "unchanged", "track": track_data}

        users_collection.update_one(
            {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
        )

        return {"status": "updated", "track": track_data}
    except Exception as e:
        print(f"⚠️ Public update playing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update last played track.")
