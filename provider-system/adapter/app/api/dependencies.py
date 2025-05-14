"""
FastAPI dependencies for the Food Department Adapter.
"""
import logging
from typing import List
from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select

from app.db.models import SessionLocal, api_keys

logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependency to verify API key in requests and return the associated tenant information
    """
    logger.info("Verifying API key")
    session = SessionLocal()
    try:
        api_key_record = session.execute(
            select(api_keys).where(api_keys.c.api_key == x_api_key)
        ).fetchone()
        
        if not api_key_record:
            logger.warning("Invalid API key provided")
            raise HTTPException(status_code=403, detail="Invalid API key")
        
        logger.info("API key verified successfully")
        return {
            "api_key": api_key_record.api_key,
            "tenant_id": api_key_record.tenant_id,
            "department": api_key_record.department
        }
    except Exception as e:
        logger.error(f"Error verifying API key: {str(e)}")
        raise
    finally:
        session.close()


from app.utils.keycloak_client import verify_token


async def require_valid_token(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1].strip()
    print(f"Extracted token: {token}")

    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=403, detail="Invalid or unauthorized token")
    return payload


def require_roles_factory(required_roles: List[str]):
    def require_roles(token: dict = Depends(require_valid_token)):
        user_roles = token.get("resource_access", {}).get("myclient",{}).get("roles", [])
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return token  # Optionally return user info
    return require_roles
