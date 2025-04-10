# backend/routes/spotify_routes.py

from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse
import spotipy

from backend.db import users_collection
from backend.auth import get_token
print("🎯 Imported get_token from backend.auth")

from backend.utils.spotify_utils import (
    get_user_profile_and_tokens,
    simplify_playlist_data,
    simplify_recent_tracks
)
from backend.utils.utils import get_artist_genres

router = APIRouter()

@router.get("/login", tags=["Spotify"], summary="Spotify login")
def login():
    from backend.utils import get_spotify_oauth
    sp_oauth = get_spotify_oauth()
    return RedirectResponse(sp_oauth.get_authorize_url())

@router.get("/callback", tags=["Spotify"], summary="Spotify callback URI")
def callback(code: str):
    profile = get_user_profile_and_tokens(code)

    users_collection.update_one(
        {"user_id": profile["user_id"]},
        {"$set": profile},
        upsert=True
    )

    return RedirectResponse(f"/onboard?user_id={profile['user_id']}")

@router.get("/refresh_token", tags=["Spotify"], summary="Get the current user's refresh token")
def refresh(refresh_token: str = Query(...)):
    from backend.utils import get_spotify_oauth
    sp_oauth = get_spotify_oauth()
    refreshed = sp_oauth.refresh_access_token(refresh_token)
    return {
        "access_token": refreshed["access_token"],
        "expires_in": refreshed["expires_in"]
    }

@router.get("/recently-played", tags=["Spotify"], summary="Get the current user's recently-played")
def get_recently_played(access_token: str = Depends(get_token), limit: int = 10):
    sp = spotipy.Spotify(auth=access_token)
    try:
        recent = sp.current_user_recently_played(limit=limit)
        return {"recently_played": simplify_recent_tracks(recent, sp, {})}
    except Exception as e:
        print(f"⚠️ Recently played error: {e}")
        return {"recently_played": False}

@router.get("/playback", tags=["Spotify"], summary="Playback control and reader")
def get_playback_state(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    try:
        playback = sp.current_playback()
        if not playback or not playback.get("item"):
            recent = sp.current_user_recently_played(limit=1)
            if not recent["items"]:
                return {"playback": False}
            track = recent["items"][0]["track"]
            return {
                "playback": {
                    "is_playing": False,
                    "device": None,
                    "volume_percent": None,
                    "track": {
                        "name": track["name"],
                        "artist": track["artists"][0]["name"],
                        "album": track["album"]["name"],
                        "external_url": track["external_urls"]["spotify"]
                    }
                }
            }

        track = playback["item"]
        return {
            "playback": {
                "is_playing": playback["is_playing"],
                "device": playback["device"]["name"],
                "volume_percent": playback["device"]["volume_percent"],
                "track": {
                    "name": track["name"],
                    "artist": track["artists"][0]["name"],
                    "album": track["album"]["name"],
                    "external_url": track["external_urls"]["spotify"],
                    "album_art_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                }
            }
        }

    except Exception as e:
        print(f"⚠️ Playback error: {e}")
        return {"playback": False}

@router.get("/playlists", tags=["Spotify"], summary="Get current user's Spotify playlists")
def get_playlists(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    raw = sp.current_user_playlists()
    return {"items": [simplify_playlist_data(p) for p in raw["items"]]}

@router.get("/top-tracks", tags=["Spotify"], summary="Get current user's top tracks playlists")
def get_top_tracks(access_token: str = Depends(get_token), limit: int = 10, time_range: str = "medium_term"):
    print("🔥 In get_top_tracks endpoint")
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    artist_genre_cache = {}

    return {
        "top_tracks": [
            {
                "name": track["name"],
                "artists": [a["name"] for a in track["artists"]],
                "album": track["album"]["name"],
                "external_url": track["external_urls"]["spotify"],
                "isrc": track.get("external_ids", {}).get("isrc"),
                "genres": get_artist_genres(sp, track["artists"], artist_genre_cache)
            }
            for track in top_tracks["items"]
        ]
    }

@router.post("/play", tags=["Spotify"], summary="Plays current track")
def start_playback(access_token: str = Depends(get_token)):
    spotipy.Spotify(auth=access_token).start_playback()
    return {"status": "playing"}

@router.post("/pause", tags=["Spotify"], summary="Pauses current track")
def pause_playback(access_token: str = Depends(get_token)):
    spotipy.Spotify(auth=access_token).pause_playback()
    return {"status": "paused"}

@router.get("/playlist-info", tags=["Spotify"], summary="Get playlist info of a song")
def get_playlist_info(user_id: str = Query(...), playlist_id: str = Query(...)):
    access_token = get_token(user_id)
    sp = spotipy.Spotify(auth=access_token)
    playlist = sp.playlist(playlist_id)
    return {
        "name": playlist["name"],
        "image": playlist["images"][0]["url"] if playlist["images"] else None
    }