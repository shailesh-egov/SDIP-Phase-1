"""
FastAPI dependencies for the Old Pension Adapter.
"""

from fastapi import Header, HTTPException
from app.core.config import API_KEY


from app.core.logger import get_logger

logger = get_logger(__name__)


async def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependency to verify API key in requests
    """
    logger.info("Verifying API key")
    try:
        if x_api_key != API_KEY:
            logger.warning("Invalid API key provided")
            raise HTTPException(status_code=403, detail="Invalid API key")
        logger.info("API key verified successfully")
    except Exception as e:
        logger.error(f"Error verifying API key: {str(e)}")
        raise
    return x_api_key