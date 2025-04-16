# backend/tests/test_user.py

def test_get_user_from_db(client, mocker):
    fake_user = {
        "user_id": "test123",
        "display_name": "Testy McTestface",
        "email": "test@example.com",
        "user_playlists": [],
        "featured_playlists": []
    }
    mocker.patch("backend.db.users_collection.find_one", return_value=fake_user)
    response = client.get("/api/user/me?user_id=test123")
    assert response.status_code == 200
    assert response.json()["user_id"] == "test123"