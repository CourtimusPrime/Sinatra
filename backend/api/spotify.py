# api/spotify.py
import spotipy
from fastapi import APIRouter, Depends, HTTPException, Query
from spotipy.exceptions import SpotifyException

from services.spotify_auth import get_artist_genres
from services.token import get_token

router = APIRouter(tags=["spotify"])


@router.get("/top-tracks")
def get_top_tracks(
    access_token: str = Depends(get_token),
    limit: int = 10,
    time_range: str = "medium_term",
):
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    artist_genre_cache = {}
    simplified = []

    for track in top_tracks["items"]:
        genres = get_artist_genres(sp, track["artists"], artist_genre_cache)

        simplified.append(
            {
                "name": track["name"],
                "artists": [a["name"] for a in track["artists"]],
                "album": track["album"]["name"],
                "external_url": track["external_urls"]["spotify"],
                "isrc": track.get("external_ids", {}).get("isrc"),
                "genres": genres,
            }
        )

    return {"top_tracks": simplified}


@router.get("/spotify-me")
def get_spotify_me(user_id: str = Query(...)):
    try:
        access_token = get_token(user_id)
        sp = spotipy.Spotify(auth=access_token)
        return sp.current_user()
    except SpotifyException as e:
        print(f"⚠️ Spotify /me error for {user_id}: {e}")
        raise HTTPException(status_code=401, detail="Failed to fetch Spotify user profile.")
