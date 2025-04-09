# backend/main.py
import sys
import os
from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
import spotipy
from backend.utils import get_spotify_oauth, get_artist_genres
from backend.db import users_collection
from backend.auth import get_token
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
sp_oauth = get_spotify_oauth()

@app.get("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)
    
@app.get("/user-playlists")
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

@app.get("/callback")
def callback(code: str):
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]
    refresh_token = token_info["refresh_token"]
    expires_at = token_info["expires_at"]

    sp = spotipy.Spotify(auth=access_token)
    user_profile = sp.current_user()
    user_id = user_profile["id"]

    # Save to DB
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "display_name": user_profile["display_name"],
            "email": user_profile["email"],
            "profile_picture": user_profile["images"][0]["url"] if user_profile["images"] else None
        }},
        upsert=True
    )

    # Frontend redirect: send user_id to frontend
    response = RedirectResponse(f"/onboard?user_id={user_id}")
    return response

@app.get("/recently-played")
def get_recently_played(
    access_token: str = Depends(get_token),
    limit: int = 10
):
    sp = spotipy.Spotify(auth=access_token)
    artist_genre_cache = {}

    try:
        recent = sp.current_user_recently_played(limit=limit)
        simplified = []

        for item in recent["items"]:
            track = item["track"]
            genres = get_artist_genres(sp, track["artists"], artist_genre_cache)

            simplified.append({
                "played_at": item["played_at"],
                "track": {
                    "name": track["name"],
                    "artists": [a["name"] for a in track["artists"]],
                    "album": track["album"]["name"],
                    "isrc": track.get("external_ids", {}).get("isrc"),
                    "external_url": track["external_urls"]["spotify"],
                    "genres": genres
                }
            })

        return {"recently_played": simplified}
    
    except Exception as e:
        print(f"⚠️ Recently played error: {e}")
        return {"recently_played": False}
    
@app.get("/playback")
def get_playback_state(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)

    try:
        playback = sp.current_playback()
        if not playback or not playback.get("item"):
            # Fallback to recently played if no current playback
            recent = sp.current_user_recently_played(limit=1)
            if not recent["items"]:
                return {"playback": False}

            recent_track = recent["items"][0]["track"]
            return {
                "playback": {
                    "is_playing": False,
                    "device": None,
                    "volume_percent": None,
                    "track": {
                        "name": recent_track["name"],
                        "artist": recent_track["artists"][0]["name"],
                        "album": recent_track["album"]["name"],
                        "external_url": recent_track["external_urls"]["spotify"]
                    }
                }
            }

        return {
            "playback": {
                "is_playing": playback["is_playing"],
                "device": playback["device"]["name"],
                "volume_percent": playback["device"]["volume_percent"],
                "track": {
                    "name": playback["item"]["name"],
                    "artist": playback["item"]["artists"][0]["name"],
                    "album": playback["item"]["album"]["name"],
                    "external_url": playback["item"]["external_urls"]["spotify"]
                }
            }
        }
    except Exception as e:
        print(f"⚠️ Playback error: {e}")
        return {"playback": False}
    

@app.get("/refresh_token")
def refresh(refresh_token: str = Query(...)):
    refreshed = sp_oauth.refresh_access_token(refresh_token)
    return {
        "access_token": refreshed["access_token"],
        "expires_in": refreshed["expires_in"]
    }

@app.get("/me")
def get_current_user(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    return sp.current_user()

@app.get("/playlists")
def get_playlists(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    raw = sp.current_user_playlists()
    
    # Simplify and return only what we need
    playlists = [
        {
            "id": p["id"],
            "name": p["name"],
            "image": p["images"][0]["url"] if p["images"] else None,
            "tracks": p["tracks"]["total"]
        }
        for p in raw["items"]
    ]
    
    return {"items": playlists}

@app.get("/users")
def get_users():
    return list(users_collection.find({}, {"_id": 0, "user_id": 1, "display_name": 1, "email": 1}))

@app.get("/top-tracks")
def get_top_tracks(
    access_token: str = Depends(get_token),
    limit: int = 10,
    time_range: str = "medium_term"
):
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    artist_genre_cache = {}
    simplified = []

    for track in top_tracks["items"]:
        genres = get_artist_genres(sp, track["artists"], artist_genre_cache)

        simplified.append({
            "name": track["name"],
            "artists": [a["name"] for a in track["artists"]],
            "album": track["album"]["name"],
            "external_url": track["external_urls"]["spotify"],
            "isrc": track.get("external_ids", {}).get("isrc"),
            "genres": genres
        })

    return {"top_tracks": simplified}

@app.post("/play")
def start_playback(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    sp.start_playback()
    return {"status": "playing"}

@app.post("/pause")
def pause_playback(access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)
    sp.pause_playback()
    return {"status": "paused"}

app.mount("/static/js", StaticFiles(directory="frontend/js"), name="frontend-js")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")

@app.get("/login-page")
def serve_login():
    return FileResponse("frontend/login.html")

@app.get("/onboard")
def serve_onboard():
    return FileResponse("frontend/onboard.html")

@app.get("/home")
def serve_home():
    return FileResponse("frontend/home.html")

@app.post("/complete-onboarding")
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

    # Save in user + public collection
    users_collection.update_one(
        {"user_id": data["user_id"]},
        {"$set": {
            "display_name": data["display_name"],
            "profile_picture": data["profile_picture"],
            "important_playlists": data["playlist_ids"],
            "onboarded": True
        }}
    )

    for pl in full_playlists:
        users_collection.update_one(
            {"public_playlists.playlist_id": pl["playlist_id"]},
            {"$set": {"public_playlists.$": pl}},
            upsert=True
        )

    return {"status": "ok"}

@app.get("/public-playlist/{playlist_id}")
def get_public_playlist(playlist_id: str):
    match = users_collection.find_one(
        {"public_playlists.playlist_id": playlist_id},
        {"public_playlists.$": 1}
    )
    if not match or "public_playlists" not in match:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return match["public_playlists"][0]

@app.get("/playlist-info")
def get_playlist_info(user_id: str = Query(...), playlist_id: str = Query(...)):
    access_token = get_token(user_id)
    sp = spotipy.Spotify(auth=access_token)
    playlist = sp.playlist(playlist_id)

    return {
        "name": playlist["name"],
        "image": playlist["images"][0]["url"] if playlist["images"] else None
    }

@app.get("/my-playlists")
def serve_my_playlists():
    return FileResponse("frontend/my-playlists.html")

@app.get("/user-genres")
def get_flat_user_genres(
    access_token: str = Depends(get_token),
    time_range: str = "short_term",  # "short_term" = past 4 weeks
    limit: int = 100
):
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    artist_genre_cache = {}
    flat_genres = []

    for track in top_tracks["items"]:
        genres = get_artist_genres(sp, track["artists"], artist_genre_cache)
        flat_genres.extend(genres)

    return {"genres": flat_genres}