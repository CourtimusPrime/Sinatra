# backend/services/session.py
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request

from db import queries as q

SESSION_COOKIE = "sinatra_session"
SESSION_DURATION = timedelta(days=7)


def create_session(spotify_id: str) -> str:
    """Create a new DB session for the user, return the opaque token."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + SESSION_DURATION
    q.create_session(spotify_id, token, expires_at)
    return token


def delete_session(session_token: str) -> None:
    q.delete_session(session_token)


def get_user_id_from_request(request: Request) -> str:
    """Extract the authenticated user's spotify_id from the session cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="Missing session cookie")
    spotify_id = q.get_session_user(token)
    if not spotify_id:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return spotify_id
