# api/public.py
import logging

import spotipy
from fastapi import APIRouter, HTTPException, Query

from db import queries as q
from services.spotify import build_track_data
from services.token import get_token_by_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["public"])


def _build_profile_response(user_id: str):
    """Return the public profile document for the given user."""
    user = q.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_playlists = q.get_saved_playlists(user_id)
    featured_playlists = q.get_featured_playlists(user_id)
    genres_data = q.get_genre_analysis(user_id)
    last_played = q.get_last_played(user_id)

    return {
        "user_id": user["user_id"],
        "display_name": user.get("display_name"),
        "profile_picture": user.get("profile_image_url"),
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played or {},
    }


@router.get("/public-profile/{user_id}")
def get_public_profile(user_id: str):
    return _build_profile_response(user_id)


@router.get("/public-profile")
def get_public_profile_query(user_id: str = Query(...)):
    return _build_profile_response(user_id)


@router.get("/public-track/{user_id}")
def get_public_track(user_id: str):
    track = q.get_last_played(user_id)
    if not track:
        return {"track": None}

    required_keys = {"id", "name", "artist", "album", "album_art_url"}
    if not isinstance(track, dict) or not required_keys.issubset(track.keys()):
        raise HTTPException(status_code=422, detail="Track data is malformed")

    return {"track": track}


@router.get("/public-genres/{user_id}")
def get_public_genres(user_id: str):
    analysis = q.get_genre_analysis(user_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No genre data found")
    return analysis


@router.get("/public-played/{user_id}")
def get_public_recently_played(user_id: str, limit: int = 1):
    try:
        access_token = get_token_by_user_id(user_id)
        sp = spotipy.Spotify(auth=access_token)

        recent = sp.current_user_recently_played(limit=limit)
        if not recent["items"]:
            return {"track": None}

        track = recent["items"][0]["track"]
        track_data = build_track_data(track, sp)

        existing = q.get_last_played(user_id)
        if existing and existing.get("id") == track_data["id"]:
            logger.debug("Track already stored, skipping update")
            return {"status": "unchanged", "track": track_data}

        q.upsert_playback(user_id, track_data)
        return {"track": track_data}
    except Exception as e:
        logger.warning("Public recently played error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch recently played track")


@router.post("/public-update-playing/{user_id}")
def public_update_playing(user_id: str):
    try:
        access_token = get_token_by_user_id(user_id)
        sp = spotipy.Spotify(auth=access_token)

        current = sp.current_playback()
        if not current or not current.get("item"):
            raise HTTPException(status_code=404, detail="nothing is currently playing")

        track_data = build_track_data(current["item"], sp)

        existing = q.get_last_played(user_id)
        if existing and existing.get("id") == track_data["id"]:
            logger.debug("Track already stored, skipping update")
            return {"status": "unchanged", "track": track_data}

        q.upsert_playback(user_id, track_data)
        return {"status": "updated", "track": track_data}
    except Exception as e:
        logger.warning("Public update playing error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update last played track")
