# backend/tests/test_spotify.py
# Validates calls to Spotify API are working, even mocked


def test_top_tracks_mocked(client, mocker):
    mocker.patch("backend.routes.spotify_routes.get_token", return_value="mock-token")
    mocker.patch(
        "backend.db.users_collection.find_one", return_value={"user_id": "test123"}
    )
    mocker.patch(
        "backend.db.users_collection.find_one",
        return_value={
            "user_id": "test123",
            "access_token": "mock-token",
            "refresh_token": "mock-refresh",
            "expires_at": 9999999999,
        },
    )

    mock_spotify = mocker.patch("spotipy.Spotify")
    mock_spotify.return_value.current_user_top_tracks.return_value = {
        "items": [
            {
                "name": "Mock Track",
                "artists": [{"name": "Mock Artist", "id": "123"}],
                "album": {
                    "name": "Mock Album",
                    "images": [],
                    "external_urls": {"spotify": "#"},
                },
                "external_urls": {"spotify": "#"},
                "external_ids": {"isrc": "XYZ"},
            }
        ]
    }
    mock_spotify.return_value.artist.return_value = {"genres": ["mock genre"]}

    response = client.get("/api/spotify/top-tracks?user_id=test123")
    print("💥", response.status_code, response.text)
    assert response.status_code == 200
    assert response.json()["top_tracks"][0]["name"] == "Mock Track"


def test_route_exists(client):
    res = client.get("/api/spotify/top-tracks?user_id=test")
    print("🎯 STATUS:", res.status_code)
    print("🎯 RESPONSE:", res.text)
