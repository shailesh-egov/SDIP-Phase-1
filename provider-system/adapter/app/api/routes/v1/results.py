from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select
import logging

from app.api.dependencies import verify_api_key
from app.services.request_processor import process_request  # Import the function
from app.db.models import SessionLocal, request_tracker
from app.core.config import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{request_id}/{part}.json")
async def get_results(request_id: str, part: str, api_key: dict = Depends(verify_api_key)):
    """
    Returns the results file for a specific request and part.
    """
    logger.info(f"Received request to fetch results for request_id: {request_id}, part: {part}")
    try:
        # Check if result file exists
        file_path = RESULTS_DIR / request_id / f"{part}.json"
        logger.debug(f"Checking if file exists at path: {file_path}")
        
        if not file_path.exists():
            logger.warning(f"Result file {part}.json not found for request {request_id}")
            raise HTTPException(status_code=404, detail=f"Result file {part}.json not found for request {request_id}")
        
        # Verify tenant_id has access to this request
        session = SessionLocal()
        logger.debug(f"Fetching request tracker record for request_id: {request_id}")
        status_record = session.execute(
            select(request_tracker).where(
                request_tracker.c.request_id == request_id,
                request_tracker.c.tenant_id == api_key["tenant_id"]
            )
        ).fetchone()
        session.close()
        
        if not status_record:
            logger.warning(f"Unauthorized access attempt for request_id: {request_id}")
            raise HTTPException(status_code=403, detail="Not authorized to access this request")
        
        logger.info(f"Returning result file {part}.json for request_id: {request_id}")
        # Return the file
        return FileResponse(
            path=str(file_path),
            media_type="application/json",
            filename=f"{part}.json"
        )
    
    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))