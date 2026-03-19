# services/spotify_auth.py
import os

from spotipy.oauth2 import SpotifyOAuth


def get_spotify_oauth(redirect_uri: str = None):
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=redirect_uri or os.getenv("PRO_CALLBACK"),
        scope="user-read-private user-read-email user-top-read user-read-recently-played user-read-playback-state streaming playlist-read-private",
        cache_path=None,
        show_dialog=True,
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
