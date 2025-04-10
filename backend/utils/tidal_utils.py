# backend/utils/tidal_utils.py

import base64
import hashlib
import os
import urllib.parse

from dotenv import load_dotenv
load_dotenv()

TIDAL_AUTH_URL = "https://login.tidal.com/authorize"
TIDAL_TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
TIDAL_CLIENT_ID = os.getenv("TIDAL_ID")
TIDAL_REDIRECT_URI = os.getenv("TIDAL_REDIRECT_URI")

SCOPES = [
    "user.read",
    "collection.read",
    "search.read",
    "playlists.read",
    "playlists.write",
    "collection.write",
    "playback",
    "recommendations.read",
    "entitlements.read"
]

def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("utf-8")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")

    return code_verifier, code_challenge

def get_tidal_auth_url(code_challenge):
    params = {
        "client_id": TIDAL_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": TIDAL_REDIRECT_URI,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "scope": " ".join(SCOPES)
    }
    return f"{TIDAL_AUTH_URL}?{urllib.parse.urlencode(params)}"