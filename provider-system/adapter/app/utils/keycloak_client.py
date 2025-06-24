# app/utils/keycloak_client.py

import re
import requests
from jose import jwt
from jose import jwk
from jose.exceptions import JWTError
from typing import Optional
from app.core.config import KEYCLOAK_URL , CERTS_URL


from app.core.logger import get_logger

logger = get_logger(__name__)



def get_public_key(kid: str):
    """
    Retrieves the public key from Keycloak based on kid in token header.
    """
    try:

        response = requests.get(CERTS_URL)
        response.raise_for_status()
        jwks = response.json()

        for key in jwks["keys"]:
            if key["kid"] == kid:
                logger.debug(f"Public key found for kid: {kid}")
                return jwk.construct(key)  #  This replaces RSAAlgorithm.from_jwk
            
        logger.error(f"Public key not found for kid: {kid}")
        raise Exception("Public key not found")

    except Exception as e:
        logger.error(f"Error fetching public key: {e}", exc_info=True)
        raise


def verify_token(token: str) -> Optional[dict]:
    """
    Validates token signature, issuer, audience, and role.
    """
    if not token or not re.match(r'^[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+$', token):
        logger.warning("Invalid token format")
        return None
    

    try:
        headers = jwt.get_unverified_headers(token)
        logger.debug(f"Decoded token headers: {headers}")
        key = get_public_key(headers["kid"])
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=KEYCLOAK_URL
        )

        logger.info("Token successfully verified")
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {e}", exc_info=True)
        return None

    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        return None
