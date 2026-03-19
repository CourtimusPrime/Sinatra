# api/playback.py
import logging

import spotipy
from fastapi import APIRouter, Depends, HTTPException, Request

from db import queries as q
from services.cookie import get_user_id_from_request
from services.spotify import build_track_data
from services.token import get_token

logger = logging.getLogger(__name__)

router = APIRouter(tags=["playback"])


@router.get("/playback")
def get_playback_state(request: Request, access_token: str = Depends(get_token)):
    user_id = get_user_id_from_request(request)

    sp = spotipy.Spotify(auth=access_token)

    try:
        playback = sp.current_playback()

        if playback and playback.get("item"):
            track_data = build_track_data(playback["item"], sp)

            existing = q.get_last_played(user_id)
            if existing and existing.get("id") == track_data["id"]:
                logger.debug("Track already stored, skipping update")
                return {"status": "unchanged", "track": track_data}

            q.upsert_playback(user_id, track_data)
            return {"playback": track_data}
        else:
            last = q.get_last_played(user_id)
            return {"playback": last}

    except Exception as e:
        logger.error("Playback error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch playback state")


@router.get("/recently-played")
def get_recently_played(request: Request, access_token: str = Depends(get_token), limit: int = 1):
    sp = spotipy.Spotify(auth=access_token)

    try:
        recent = sp.current_user_recently_played(limit=limit)
        if not recent["items"]:
            return {"track": None}

        track = recent["items"][0]["track"]
        track_data = build_track_data(track, sp)

        user_id = None
        cookie_val = request.cookies.get("sinatra_user_id")
        if cookie_val:
            try:
                user_id = get_user_id_from_request(request)
            except HTTPException:
                user_id = None

        if user_id:
            existing = q.get_last_played(user_id)
            if existing and existing.get("id") == track_data["id"]:
                logger.debug("Track already stored, skipping update")
                return {"status": "unchanged", "track": track_data}
            q.upsert_playback(user_id, track_data)

        return {"track": track_data}

    except Exception as e:
        logger.warning("Recently played error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch recently played track")


@router.get("/now-playing")
def now_playing(request: Request, access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)

    try:
        current = sp.current_playback()
        if not current or not current.get("item"):
            return {"track": None}

        track = current["item"]
        track_data = build_track_data(track, sp)

        return {"track": track_data}

    except Exception as e:
        logger.warning("Now playing error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to fetch now playing track")


@router.post("/update-playing")
def update_playing(request: Request, access_token: str = Depends(get_token)):
    user_id = get_user_id_from_request(request)

    sp = spotipy.Spotify(auth=access_token)

    try:
        current = sp.current_playback()
        if not current or not current.get("item"):
            raise HTTPException(status_code=404, detail="Nothing is currently playing")

        track_data = build_track_data(current["item"], sp)

        existing = q.get_last_played(user_id)
        if existing and existing.get("id") == track_data["id"]:
            logger.debug("Track already stored, skipping update")
            return {"status": "unchanged", "track": track_data}

        q.upsert_playback(user_id, track_data)
        return {"status": "updated", "track": track_data}

    except Exception as e:
        logger.error("Update playing error: %s", e)
        raise HTTPException(status_code=500, detail="Failed to update last played track")


@router.get("/check-recent")
def check_recent_track(request: Request):
    user_id = get_user_id_from_request(request)
    track = q.get_last_played(user_id)
    return {"track": track}
