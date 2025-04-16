# backend/tests/test_spotify.py
# Validates calls to Spotify API are working, even mocked

def test_top_tracks_mocked(client, mocker):
    mocker.patch("backend.auth.token_handler.get_token", return_value="fake-access-token")
    mock_spotify = mocker.patch("spotipy.Spotify")
    mock_spotify.return_value.current_user_top_tracks.return_value = {
        "items": [{
            "name": "Mock Track",
            "artists": [{"name": "Mock Artist", "id": "123"}],
            "album": {"name": "Mock Album", "images": [], "external_urls": {"spotify": "#"}},
            "external_urls": {"spotify": "#"},
            "external_ids": {"isrc": "XYZ"}
        }]
    }
    mock_spotify.return_value.artist.return_value = {"genres": ["mock genre"]}

    response = client.get("/api/spotify/top-tracks")
    assert response.status_code == 200
    assert response.json()["top_tracks"][0]["name"] == "Mock Track"