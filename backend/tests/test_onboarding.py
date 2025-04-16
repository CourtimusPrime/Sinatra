# backend/tests/test_onboarding.py
# Tests the onboarding process → /complete-onboarding
import pytest

def test_complete_onboarding(client, mocker):
    # Patch FIRST
    mocker.patch("backend.routes.user.get_token", return_value="mock-token")
    mock_spotify = mocker.patch("spotipy.Spotify")

    # Playlist stub
    mock_spotify.return_value.playlist.return_value = {
        "name": "Fake Playlist",
        "images": [{"url": "#"}],
        "tracks": {"items": [{
            "track": {
                "name": "Song",
                "artists": [{"name": "Artist"}],
                "album": {"name": "Album", "images": [{"url": "#"}]},
                "external_ids": {"isrc": "XYZ"},
                "id": "abc123"
            }
        }]}
    }

    mocker.patch("backend.db.users_collection.update_one")

    # ⬇️ This should be sent AFTER mocks are in place
    payload = {
        "user_id": "123",
        "display_name": "Testy",
        "profile_picture": "#",
        "playlist_ids": ["pl1"],
        "featured_playlists": []
    }

    response = client.post("/api/user/complete-onboarding", json=payload)
    print("💥", response.status_code, response.text)
    assert response.status_code == 200

def test_onboarding_route_exists(client):
    res = client.post("/api/user/complete-onboarding", json={})
    print("🎯 STATUS:", res.status_code)
    print("🎯 RESPONSE:", res.text)