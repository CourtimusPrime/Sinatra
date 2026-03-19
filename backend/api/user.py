# api/user.py
from datetime import datetime

import spotipy
from fastapi import APIRouter, Body, HTTPException, Query, Request
from fastapi.responses import JSONResponse

from api.genres import get_genres
from db.mongo import playlists_collection, users_collection
from services.cookie import get_user_id_from_request
from services.music.track_utils import apply_meta_gradients
from services.token import get_token

router = APIRouter(tags=["user"])


@router.get("/me")
def get_me(request: Request):
    user_id = get_user_id_from_request(request)

    user = users_collection.find_one({"user_id": user_id})

    if not user or "display_name" not in user:
        # Attempt auto-registration via Spotify API
        try:
            access_token = get_token(request)
            sp = spotipy.Spotify(auth=access_token)
            sp_user = sp.current_user()

            display_name = sp_user["display_name"]
            profile_image = sp_user["images"][0]["url"] if sp_user.get("images") else None

            new_user = {
                "user_id": user_id,
                "display_name": display_name,
                "profile_image_url": profile_image,
                "theme": "default",
            }

            users_collection.update_one({"user_id": user_id}, {"$set": new_user}, upsert=True)
            return new_user

        except Exception as e:
            print(f"⚠️ Failed to auto-register user {user_id}: {e}")
            raise HTTPException(status_code=404, detail="User not found and cannot be registered")

    return {
        "user_id": user["user_id"],
        "display_name": user["display_name"],
        "profile_image_url": user.get("profile_image_url"),
        "theme": user.get("theme", "default"),
    }


@router.get("/users")
def get_users():
    return list(users_collection.find({}, {"_id": 0, "user_id": 1, "display_name": 1, "email": 1}))


@router.post("/register")
def register_user(data: dict = Body(...)):
    user_id = data.get("user_id") or data.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    display_name = data.get("display_name")
    profile_picture = data.get("profile_picture")
    selected_playlists = data.get("selected_playlists", [])
    featured_ids = [p.get("id") for p in data.get("featured_playlists", [])]

    sp = spotipy.Spotify(auth=get_token(user_id))
    enriched = []

    for pl in selected_playlists:
        try:
            playlist = sp.playlist(pl["id"])
            enriched.append(
                {
                    "id": pl["id"],
                    "name": playlist["name"],
                    "image": (playlist["images"][0]["url"] if playlist["images"] else None),
                    "tracks": playlist["tracks"]["total"],
                    "external_url": playlist["external_urls"]["spotify"],
                }
            )
        except Exception as e:
            print(f"⚠️ Failed to enrich playlist {pl['id']}: {e}")
            continue

    user_doc = {
        "user_id": user_id,
        "display_name": display_name,
        "profile_picture": profile_picture,
        "playlists": {
            "all": enriched,
            "featured": featured_ids,
        },
        "created_at": datetime.utcnow(),
        "registered": True,
    }

    users_collection.update_one({"user_id": user_id}, {"$set": user_doc}, upsert=True)

    # Optional: trigger last_played and genre analysis
    try:
        from api.genres import get_genres

        playback = sp.current_playback()
        if playback and playback.get("item"):
            artist = playback["item"]["artists"][0]
            artist_data = sp.artist(artist["id"])
            track_data = {
                "track": {
                    "id": playback["item"]["id"],
                    "name": playback["item"]["name"],
                    "artist": artist["name"],
                    "album": playback["item"]["album"]["name"],
                    "external_url": playback["item"]["external_urls"]["spotify"],
                    "album_art_url": (
                        playback["item"]["album"]["images"][0]["url"]
                        if playback["item"]["album"]["images"]
                        else None
                    ),
                    "genres": artist_data.get("genres", []),
                }
            }

            users_collection.update_one(
                {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
            )
    except Exception as e:
        print("⚠️ Playback fetch failed:", e)

    try:
        get_genres(user_id=user_id, refresh=True)
    except Exception as e:
        print("⚠️ Genre analysis failed during registration:", e)

    return {"status": "success", "message": "User registered and initialized"}


@router.delete("/delete-user")
def delete_user(request: Request, user_id: str = Query(...)):
    print(f"🗑️ Deleting user: {user_id}")

    users_collection.delete_one({"user_id": user_id})
    playlists_collection.delete_one({"user_id": user_id})

    response = JSONResponse(content={"status": "deleted"})
    response.delete_cookie("sinatra_user_id", path="/")
    return response


@router.get("/session")
def get_session(request: Request):
    """Return combined user profile and dashboard data."""
    user_id = get_user_id_from_request(request)
    user = users_collection.find_one({"user_id": user_id})

    if not user or "display_name" not in user:
        try:
            access_token = get_token(request)
            sp = spotipy.Spotify(auth=access_token)
            sp_user = sp.current_user()

            display_name = sp_user["display_name"]
            profile_image = sp_user["images"][0]["url"] if sp_user.get("images") else None

            new_user = {
                "user_id": user_id,
                "display_name": display_name,
                "profile_image_url": profile_image,
                "theme": "default",
            }

            users_collection.update_one({"user_id": user_id}, {"$set": new_user}, upsert=True)
            user = new_user
        except Exception as e:
            print(f"⚠️ Failed to auto register user {user_id}: {e}")
            raise HTTPException(status_code=404, detail="User not found and cannot be registered.")

    playlists_data = user.get("playlists", {})
    all_playlists = playlists_data.get("all", [])
    featured_ids = playlists_data.get("featured", [])
    playlist_lookup = {pl.get("id") or pl.get("playlist_id"): pl for pl in all_playlists}
    featured_playlists = [
        playlist_lookup.get(pid) for pid in featured_ids if pid in playlist_lookup
    ]

    genres_data = get_genres(request)
    last_played = apply_meta_gradients(user.get("last_played_track", {}))

    return {
        "user_id": user["user_id"],
        "display_name": user.get("display_name"),
        "profile_image_url": user.get("profile_image_url"),
        "theme": user.get("theme", "default"),
        "playlists": {
            "all": all_playlists,
            "featured": featured_playlists,
        },
        "genres": genres_data,
        "last_played": last_played,
    }
