# backend/utils.py

import os
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

required_env_vars = ["SPOTIPY_CLIENT_ID", "SPOTIPY_CLIENT_SECRET", "SPOTIPY_REDIRECT_URI", "MONGODB_URI"]
for var in required_env_vars:
    if not os.getenv(var):
        raise Exception(f"Missing environment variable: {var}")

def get_spotify_oauth():
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="user-read-private user-read-email user-read-playback-state user-modify-playback-state playlist-read-private user-top-read user-read-recently-played"
    )

def get_artist_genres(sp, artists, cache):
    genres = set()
    for artist in artists:
        artist_id = artist["id"]
        if artist_id not in cache:
            artist_info = sp.artist(artist_id)
            cache[artist_id] = artist_info.get("genres", [])
        genres.update(cache[artist_id])
    return list(genres)