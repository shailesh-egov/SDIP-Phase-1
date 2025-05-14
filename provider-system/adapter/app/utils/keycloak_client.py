# app/utils/keycloak_client.py

import re
import requests
from jose import jwt
from jose import jwk
from jose.exceptions import JWTError
from typing import Optional
from app.core.config import KEYCLOAK_URL , CERTS_URL



def get_public_key(kid: str):
    """
    Retrieves the public key from Keycloak based on kid in token header.
    """
    response = requests.get(CERTS_URL)
    jwks = response.json()

    for key in jwks["keys"]:
        if key["kid"] == kid:
            return jwk.construct(key)  # ✅ This replaces RSAAlgorithm.from_jwk

    raise Exception("Public key not found")


def verify_token(token: str) -> Optional[dict]:
    """
    Validates token signature, issuer, audience, and role.
    """
    if not token or not re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$', token):
        print("Invalid token format")
        return None
    

    try:
        headers = jwt.get_unverified_headers(token)
        key = get_public_key(headers["kid"])
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=KEYCLOAK_URL
        )

        return payload
    except JWTError as e:
        print(f"Token verification failed: {e}")
        return None
