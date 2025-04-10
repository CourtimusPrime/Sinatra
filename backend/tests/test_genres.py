# backend/tests/test_genres.py

def test_get_top_tracks_with_mocked_spotify(client, mocker):
    fake_tracks = {
        "items": [
            {
                "name": "Test Track",
                "artists": [{"name": "Test Artist", "id": "1"}],
                "album": {"name": "Test Album", "images": []},
                "external_urls": {"spotify": "https://..."},
                "external_ids": {"isrc": "XYZ"}
            }
        ]
    }

    # 🛠️ Mock both the Spotify client and the token dependency
    mocker.patch("backend.routes.spotify_routes.get_token", return_value="mock-access-token")
    mock_spotify = mocker.patch("spotipy.Spotify")
    mock_spotify.return_value.current_user_top_tracks.return_value = fake_tracks
    mock_spotify.return_value.artist.return_value = {"genres": ["indie pop"]}

    response = client.get("/top-tracks", params={"user_id": "fake"})
    
    # ✅ Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["top_tracks"][0]["name"] == "Test Track"
    assert "indie pop" in data["top_tracks"][0]["genres"]