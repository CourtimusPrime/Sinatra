# backend/services/cookie.py
import base64
import hashlib
import hmac
import os

from fastapi import HTTPException, Request

_NODE_ENV = os.getenv("NODE_ENV", "development").lower()

SECRET = os.getenv("COOKIE_SECRET")
if not SECRET:
    if _NODE_ENV == "development":
        import secrets
        SECRET = secrets.token_hex(32)
    else:
        raise RuntimeError("COOKIE_SECRET environment variable must be set in production")


def _sign(value: str) -> str:
    sig = hmac.new(SECRET.encode(), value.encode(), hashlib.sha256).digest()
    # Base64-encode the binary signature
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def encode(user_id: str) -> str:
    signature = _sign(user_id)
    return f"{user_id}.{signature}"


def decode(cookie_value: str) -> str:
    try:
        user_id, signature = cookie_value.rsplit(".", 1)
    except ValueError:
        raise ValueError("🍪 Wrong cookie format")
    expected = _sign(user_id)
    if not hmac.compare_digest(signature, expected):
        raise ValueError("🖊️ Wrong cookie signature!")
    return user_id


def get_user_id_from_request(request: Request) -> str:
    cookie = request.cookies.get("sinatra_user_id")
    if not cookie:
        raise HTTPException(status_code=401, detail="🤷‍♂️ Missing sinatra_user_id cookie")
    try:
        return decode(cookie)
    except ValueError:
        raise HTTPException(status_code=401, detail="🙅‍♂️ Invalid sinatra_user_id cookie")
