# backend/tests/test_auth.py
# Test token refreshing logic via get_token()

def test_token_refresh_logic(mocker):
    mock_user = {
        "user_id": "123",
        "access_token": "oldtoken",
        "refresh_token": "refreshtoken",
        "expires_at": 0
    }

    mocker.patch("backend.db.users_collection.find_one", return_value=mock_user)
    mock_spotify_oauth = mocker.Mock()
    mock_spotify_oauth.is_token_expired.return_value = True
    mock_spotify_oauth.refresh_access_token.return_value = {
        "access_token": "newtoken",
        "expires_at": 9999999999
    }
    mocker.patch("backend.auth.token_handler.get_spotify_oauth", return_value=mock_spotify_oauth)

    from backend.auth.token_handler import get_token
    token = get_token(user_id="123")
    assert token == "newtoken"