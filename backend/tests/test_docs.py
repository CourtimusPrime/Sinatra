# backend/tests/test_docs.py
def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert b"Swagger UI" in response.content