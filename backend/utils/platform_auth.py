# utils/platform_auth.py

import base64
import hashlib
import os
import urllib.parse

def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("utf-8")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("utf-8")
    return code_verifier, code_challenge

def build_auth_url(base_url, client_id, redirect_uri, code_challenge, scopes):
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
        "scope": " ".join(scopes)
    }
    return f"{base_url}?{urllib.parse.urlencode(params)}"