# backend/tests/test_routes.py

def test_top_tracks(client):
    print("🧪 Sending request to /top-tracks")
    response = client.get("/top-tracks", params={"user_id": "fake"})
    print("📦 Got response:", response.status_code, response.text)
    
    assert response.status_code == 200  # Or whatever you're expecting