# app/utils/keycloak_client.py

import requests
from jose import jwt
from jose.exceptions import JWTError
from typing import Optional
import time
from app.core.config import CLIENT_ID, CLIENT_SECRET, TOKEN_URL


_token_cache = {}

def get_token(username: str, password: str) -> str:
    """
    Fetch or reuse cached Keycloak token
    """
    cache_key = f"{username}"
    current_time = int(time.time())

    if cache_key in _token_cache:
        token_info = _token_cache[cache_key]
        if current_time < token_info["expires_at"]:
            return token_info["token"]

    # Get new token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "password",
        "username": username,
        "password": password
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()

    token_data = response.json()
    token = token_data["access_token"]

    # Decode token to get expiration
    decoded = jwt.get_unverified_claims(token)
    expires_in = decoded.get("exp", current_time + 300)  # fallback 5 mins
    _token_cache[cache_key] = {
        "token": token,
        "expires_at": expires_in - 10  # buffer 10 seconds
    }

    return token





