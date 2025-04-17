# backend/services/spotify_service.py

import spotipy
from backend.utils import get_spotify_oauth, get_artist_genres


def get_user_profile_and_tokens(code: str):
    sp_oauth = get_spotify_oauth()
    token_info = sp_oauth.get_access_token(code)
    access_token = token_info["access_token"]
    refresh_token = token_info["refresh_token"]
    expires_at = token_info["expires_at"]

    sp = spotipy.Spotify(auth=access_token)
    profile = sp.current_user()

    return {
        "user_id": profile["id"],
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "display_name": profile["display_name"],
        "email": profile["email"],
        "profile_picture": (
            profile["images"][0]["url"]
            if profile.get("images") and profile["images"]
            else None
        ),
    }


def simplify_playlist_data(playlist):
    return {
        "id": playlist["id"],
        "name": playlist["name"],
        "image": playlist["images"][0]["url"] if playlist["images"] else None,
        "tracks": playlist["tracks"]["total"],
    }


def simplify_recent_tracks(recent, sp, genre_cache):
    simplified = []
    for item in recent["items"]:
        track = item["track"]
        genres = get_artist_genres(sp, track["artists"], genre_cache)
        simplified.append(
            {
                "played_at": item["played_at"],
                "track": {
                    "name": track["name"],
                    "artists": [a["name"] for a in track["artists"]],
                    "album": track["album"]["name"],
                    "isrc": track.get("external_ids", {}).get("isrc"),
                    "external_url": track["external_urls"]["spotify"],
                    "genres": genres,
                },
            }
        )
    return simplified
