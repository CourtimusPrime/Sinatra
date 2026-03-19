# api/user.py
import logging

import spotipy
from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from db import queries as q
from services.cookie import get_user_id_from_request
from services.music.track_utils import apply_meta_gradients
from services.token import get_token, get_token_by_user_id

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])


@router.get("/me")
def get_me(request: Request):
    user_id = get_user_id_from_request(request)

    user = q.get_user(user_id)

    if not user or not user.get("display_name"):
        try:
            access_token = get_token(request)
            sp = spotipy.Spotify(auth=access_token)
            sp_user = sp.current_user()

            display_name = sp_user["display_name"]
            profile_image = sp_user["images"][0]["url"] if sp_user.get("images") else None

            user = q.upsert_user(user_id, display_name, profile_image)
            return user

        except Exception as e:
            logger.warning("Failed to auto-register user %s: %s", user_id, e)
            raise HTTPException(status_code=404, detail="User not found and cannot be registered")

    return {
        "user_id": user["user_id"],
        "display_name": user["display_name"],
        "profile_image_url": user.get("profile_image_url"),
        "theme": user.get("theme", "default"),
    }


@router.post("/register")
def register_user(request: Request, data: dict = Body(...)):
    cookie_user_id = get_user_id_from_request(request)
    user_id = data.get("user_id") or data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")
    if user_id != cookie_user_id:
        raise HTTPException(status_code=403, detail="Cannot register a different user")

    display_name = data.get("display_name")
    profile_picture = data.get("profile_picture")
    selected_playlists = data.get("selected_playlists", [])
    featured_ids = [p.get("id") for p in data.get("featured_playlists", [])]

    access_token = get_token_by_user_id(user_id)
    sp = spotipy.Spotify(auth=access_token)
    enriched = []

    for pl in selected_playlists:
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
            logger.warning("Failed to enrich playlist %s: %s", pl["id"], e)
            continue

    # Update user profile
    q.upsert_user(user_id, display_name, profile_picture)
    q.set_user_registered(user_id)

    # Save playlists
    if enriched:
        q.add_saved_playlists(user_id, enriched)

    # Set featured playlists
    if featured_ids:
        q.update_featured_playlists(user_id, featured_ids)

    # Optional: store current playback
    try:
        from services.spotify import build_track_data

        playback = sp.current_playback()
        if playback and playback.get("item"):
            track_data = build_track_data(playback["item"], sp)
            q.upsert_playback(user_id, track_data)
    except Exception as e:
        logger.debug("Playback fetch during registration failed: %s", e)

    # Optional: trigger genre analysis
    try:
        from api.genres import analyze_user_genres

        analyze_user_genres(user_id, access_token)
    except Exception as e:
        logger.debug("Genre analysis during registration failed: %s", e)

    return {"status": "success", "message": "User registered and initialized"}


@router.delete("/delete-user")
def delete_user(request: Request, user_id: str = Query(...)):
    cookie_user_id = get_user_id_from_request(request)
    if user_id != cookie_user_id:
        raise HTTPException(status_code=403, detail="Cannot delete a different user")

    q.delete_user(user_id)

    response = JSONResponse(content={"status": "deleted"})
    response.delete_cookie("sinatra_user_id", path="/")
    return response


@router.get("/session")
def get_session(request: Request):
    """Return combined user profile and dashboard data."""
    user_id = get_user_id_from_request(request)
    user = q.get_user(user_id)

    if not user or not user.get("display_name"):
        try:
            access_token = get_token(request)
            sp = spotipy.Spotify(auth=access_token)
            sp_user = sp.current_user()

            display_name = sp_user["display_name"]
            profile_image = sp_user["images"][0]["url"] if sp_user.get("images") else None

            user = q.upsert_user(user_id, display_name, profile_image)
        except Exception as e:
            logger.warning("Failed to auto-register user %s: %s", user_id, e)
            raise HTTPException(status_code=404, detail="User not found and cannot be registered.")

    all_playlists = q.get_saved_playlists(user_id)
    featured_playlists = q.get_featured_playlists(user_id)

    genres_data = q.get_genre_analysis(user_id)
    last_played = apply_meta_gradients(q.get_last_played(user_id) or {})

    return {
        "user_id": user["user_id"],
        "display_name": user.get("display_name"),
        "profile_image_url": user.get("profile_image_url"),
        "theme": user.get("theme", "default"),
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played,
    }
