# backend/tests/test_onboarding.py
# Tests the onboarding process → /complete-onboarding
def test_complete_onboarding(client, mocker):
    mocker.patch("backend.auth.token_handler.get_token", return_value="mock-token")
    mock_spotify = mocker.patch("spotipy.Spotify")

    mock_spotify.return_value.playlist.return_value = {
        "name": "Fake Playlist",
        "images": [{"url": "#"}],
        "tracks": {"items": [{"track": {
            "name": "Song", "artists": [{"name": "Artist"}],
            "album": {"name": "Album", "images": [{"url": "#"}]},
            "external_ids": {"isrc": "XYZ"},
            "id": "abc123"
        }}]}
    }

    mocker.patch("backend.db.users_collection.update_one")
    payload = {
        "user_id": "123",
        "display_name": "Testy",
        "profile_picture": "#",
        "playlist_ids": ["pl1"],
        "featured_playlists": []
    }

    response = client.post("/api/user/complete-onboarding", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"