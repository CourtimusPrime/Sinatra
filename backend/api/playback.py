# api/playback.py
import spotipy
from fastapi import APIRouter, Depends, HTTPException, Request

from db.mongo import users_collection
from services.cookie import get_user_id_from_request
from services.spotify import build_track_data
from services.token import get_token

router = APIRouter(tags=["playback"])


@router.get("/playback")
def get_playback_state(request: Request, access_token: str = Depends(get_token)):
    user_id = get_user_id_from_request(request)

    sp = spotipy.Spotify(auth=access_token)

    try:
        playback = sp.current_playback()

        if playback and playback.get("item"):
            track_data = build_track_data(playback["item"], sp)

            existing = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
            if existing and existing.get("last_played_track", {}).get("id") == track_data["id"]:
                print("🟡 Track already stored, skipping update.")
                return {"status": "unchanged", "track": track_data}

            users_collection.update_one(
                {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
            )
            return {"playback": track_data}
        else:
            user = users_collection.find_one({"user_id": user_id})
            return {"playback": user.get("last_played_track", None)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recently-played")
def get_recently_played(request: Request, access_token: str = Depends(get_token), limit: int = 1):
    sp = spotipy.Spotify(auth=access_token)

    try:
        recent = sp.current_user_recently_played(limit=limit)
        if not recent["items"]:
            return {"track": None}

        track = recent["items"][0]["track"]
        track_data = build_track_data(track, sp)

        user_id_cookie = request.cookies.get("sinatra_user_id")
        user_id = None
        if user_id_cookie:
            try:
                user_id = get_user_id_from_request(request)
            except HTTPException:
                user_id = None
        if user_id:
            existing = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
            if existing and existing.get("last_played_track", {}).get("id") == track_data["id"]:
                print("🟡 Track already stored, skipping update.")
                return {"status": "unchanged", "track": track_data}
            users_collection.update_one(
                {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
            )

        return {"track": track_data}

    except Exception as e:
        print(f"⚠️ Recently played error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch recently played track")


@router.get("/now-playing")
def now_playing(request: Request, access_token: str = Depends(get_token)):
    sp = spotipy.Spotify(auth=access_token)

    try:
        current = sp.current_playback()
        if not current or not current.get("item"):
            return {"track": None}

        track = current["item"]
        track_data = build_track_data(track, sp)

        return {"track": track_data}

    except Exception as e:
        print(f"⚠️ Now playing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch now playing track")


@router.post("/update-playing")
def update_playing(request: Request, access_token: str = Depends(get_token)):
    user_id = get_user_id_from_request(request)

    sp = spotipy.Spotify(auth=access_token)

    try:
        current = sp.current_playback()
        if not current or not current.get("item"):
            raise HTTPException(status_code=404, detail="Nothing is currently playing")

        print("🎵 Current playback found")
        track_data = build_track_data(current["item"], sp)
        print("✅ Track data built:", track_data["name"], track_data["id"])

        existing = users_collection.find_one({"user_id": user_id}, {"last_played_track": 1})
        if existing and existing.get("last_played_track", {}).get("id") == track_data["id"]:
            print("🟡 Track already stored, skipping update.")
            return {"status": "unchanged", "track": track_data}

        result = users_collection.update_one(
            {"user_id": user_id}, {"$set": {"last_played_track": track_data}}
        )
        print("✅ Mongo update result:", result.raw_result)

        return {"status": "updated", "track": track_data}

    except Exception as e:
        print(f"❌ Update playing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update last played track")


@router.get("/check-recent")
def check_recent_track(request: Request):
    user_id = get_user_id_from_request(request)

    user = users_collection.find_one({"user_id": user_id})
    return {"track": user.get("last_played_track")}
