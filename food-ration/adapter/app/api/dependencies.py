"""
FastAPI dependencies for the Food Department Adapter.
"""
from fastapi import Header, HTTPException
from sqlalchemy import select

from app.db.models import SessionLocal, api_keys

async def verify_api_key(x_api_key: str = Header(...)):
    """
    Dependency to verify API key in requests and return the associated tenant information
    """
    session = SessionLocal()
    api_key_record = session.execute(
        select([api_keys]).where(api_keys.c.api_key == x_api_key)
    ).fetchone()
    session.close()
    
    if not api_key_record:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    return {
        "api_key": api_key_record.api_key,
        "tenant_id": api_key_record.tenant_id,
        "department": api_key_record.department
    }