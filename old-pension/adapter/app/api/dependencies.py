"""
FastAPI dependencies for the Old Pension Adapter.
"""
from fastapi import Header, HTTPException
from app.core.config import API_KEY

async def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependency to verify API key in requests
    """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key