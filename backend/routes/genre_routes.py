# backend/routes/genre_routes.py

from fastapi import APIRouter, Query, Depends
import spotipy
from backend.auth import get_token
from backend.genres import genre_wizard
from backend.utils import get_artist_genres

router = APIRouter()

@router.get("/test-genres")
def test_genres(user_id: str = Query(...)):
    access_token = get_token(user_id)
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=50, time_range="short_term")

    artist_genre_cache = {}
    flat_genres = []

    for track in top_tracks["items"]:
        genres = get_artist_genres(sp, track["artists"], artist_genre_cache)
        flat_genres.extend(genres)

    freq = genre_wizard.genre_frequency(flat_genres)
    highest = genre_wizard.genre_highest(freq)
    paths = [genre_wizard.get_lineage(g) for g in flat_genres]
    tags = genre_wizard.tag_genre_levels(flat_genres)
    sunburst = genre_wizard.build_sunburst_tree(freq)
    summary = genre_wizard.generate_user_summary(freq)

    return {
        "input": flat_genres,
        "frequency": freq,
        "highest": highest,
        "paths": paths,
        "tagged": tags,
        "sunburst": sunburst,
        "summary": summary
    }

@router.get("/user-genres")
def get_flat_user_genres(access_token: str = Depends(get_token), time_range: str = "short_term", limit: int = 50):
    sp = spotipy.Spotify(auth=access_token)
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)

    artist_genre_cache = {}
    flat_genres = []

    for track in top_tracks["items"]:
        genres = get_artist_genres(sp, track["artists"], artist_genre_cache)
        flat_genres.extend(genres)

    return {"genres": flat_genres}