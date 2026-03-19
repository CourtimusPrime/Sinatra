# api/genres.py
import json
import traceback
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from db.mongo import users_collection
from services.cookie import get_user_id_from_request
from services.music import wizard
from services.music.meta_gradients import gradients
from services.music.wizard import get_gradient_for_genre
from services.token import get_token, get_token_by_user_id

router = APIRouter(tags=["genres"])

GENRE_MAP_PATH = Path(__file__).resolve().parent.parent / "services" / "music" / "genre-map.json"


@router.get("/genres")
def get_genres(request: Request, refresh: bool = False):
    user_id = get_user_id_from_request(request)
    try:
        access_token = get_token(request)
        return analyze_user_genres(user_id, access_token)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Genre analysis failed: {str(e)}")


@router.post("/refresh_genres")
def refresh_genre_analysis(payload: dict):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    users_collection.update_one(
        {"user_id": user_id},
        {"$unset": {"genre_analysis": "", "genre_last_updated": ""}},
    )

    try:
        access_token = get_token_by_user_id(user_id)
        return analyze_user_genres(user_id, access_token)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.get("/meta-gradients")
def get_meta_gradients():
    return gradients


def analyze_user_genres(user_id: str, access_token: str):
    import spotipy

    sp = spotipy.Spotify(auth=access_token)

    # Fetch top 200 artists
    top_artists = []
    for offset in (0, 50, 100, 150):
        try:
            batch = sp.current_user_top_artists(limit=50, offset=offset, time_range="short_term")
            top_artists.extend(batch.get("items", []))
        except Exception as e:
            print(f"⚠️ Failed to fetch top artists at offset {offset}: {e}")

    # Extract genres
    flat_genres = []
    for artist in top_artists:
        flat_genres.extend([g.strip().lower() for g in artist.get("genres", [])])

    print("🎯 Combined raw genres from top 200 artists:", flat_genres[:20])

    raw_highest = wizard.genre_highest(flat_genres)
    sub_genres_raw = wizard.genre_frequency(flat_genres)

    total = sum(raw_highest.values()) or 1
    meta_genres = {
        genre: {
            "portion": round((count / total) * 100, 1),
            "gradient": get_gradient_for_genre(genre),
        }
        for genre, count in raw_highest.items()
    }

    try:
        with open(GENRE_MAP_PATH) as f:
            genre_map = json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to load genre map.")

    sub_genres = {}
    total_subgenre_count = sum(sub_genres_raw.values()) or 1
    for genre, count in sub_genres_raw.items():
        portion = round((count / total_subgenre_count) * 100, 1)
        parent = genre_map.get(genre.lower(), "other")
        sub_genres[genre] = {
            "portion": portion,
            "parent_genre": parent,
            "gradient": get_gradient_for_genre(parent),
        }

    sorted_subs = sorted(sub_genres.items(), key=lambda x: -x[1]["portion"])
    top_sub = next(
        (g for g, _ in sorted_subs if genre_map.get(g.lower(), "") != g.lower()),
        sorted_subs[0][0] if sorted_subs else None,
    )
    top_meta = genre_map.get(top_sub.lower(), "other") if top_sub else None

    result = {
        "sub_genres": dict(sorted(sub_genres.items(), key=lambda x: -x[1]["portion"])[:10]),
        "meta_genres": dict(sorted(meta_genres.items(), key=lambda x: -x[1]["portion"])[:10]),
        "top_subgenre": {
            "sub_genre": top_sub,
            "parent_genre": top_meta,
            "gradient": get_gradient_for_genre(top_meta),
        },
    }

    users_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "genre_analysis": result,
                "genre_last_updated": datetime.now(UTC),
            }
        },
        upsert=True,
    )

    return result
