# backend/tests/tes_server.py
# Checks if the server boots, routes are live, and docs work

def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content

def test_ping(client):
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"