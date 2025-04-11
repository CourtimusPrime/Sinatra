# backend/tests/test_spotify.py

def test_playlists_missing_token_returns_422(client):
    response = client.get("/playlists")
    assert response.status_code == 422  # missing access_token (Query param or auth header)

    