"""
FastAPI dependencies for the Food Department Adapter.
"""
import logging
from fastapi import Header, HTTPException
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