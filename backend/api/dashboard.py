# api/dashboard.py
import logging

from fastapi import APIRouter, HTTPException, Request

from db import queries as q
from services.cookie import get_user_id_from_request
from services.music.track_utils import apply_meta_gradients

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(request: Request):
    user_id = get_user_id_from_request(request)
    user = q.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_playlists = q.get_saved_playlists(user_id)
    featured_playlists = q.get_featured_playlists(user_id)

    genres_data = q.get_genre_analysis(user_id)
    last_played = apply_meta_gradients(q.get_last_played(user_id) or {})

    return {
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played,
    }
