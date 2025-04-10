# tests/spotify.py

#Tests spotify routes

def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content

def test_playlists_requires_auth(client):
    response = client.get("/playlists")
    assert response.status_code == 422  # missing access_token (Query param or auth header)

    