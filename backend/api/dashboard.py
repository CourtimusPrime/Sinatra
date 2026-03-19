# api/dashboard.py
from fastapi import APIRouter, HTTPException, Request

from api.genres import get_genres
from db.mongo import users_collection
from services.cookie import get_user_id_from_request
from services.music.track_utils import apply_meta_gradients

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(request: Request):
    user_id = get_user_id_from_request(request)
    print(f"🍪 /dashboard cookie received: sinatra_user_id = {user_id}")

    doc = users_collection.find_one({"user_id": user_id})
    if not doc:
        print(f"❌ /dashboard: user not found in DB for user_id = {user_id}")
        raise HTTPException(status_code=404, detail="User not found")

    playlists_data = doc.get("playlists", {})
    all_playlists = playlists_data.get("all", [])
    featured_ids = playlists_data.get("featured", [])

    # Create a lookup for faster matching
    playlist_lookup = {pl.get("id") or pl.get("playlist_id"): pl for pl in all_playlists}
    featured_playlists = [
        playlist_lookup.get(pid) for pid in featured_ids if pid in playlist_lookup
    ]

    print(f"✅ /dashboard success for user_id = {user_id}")
    genres_data = get_genres(request)
    last_played = apply_meta_gradients(doc.get("last_played_track", {}))

    return {
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played,
    }
