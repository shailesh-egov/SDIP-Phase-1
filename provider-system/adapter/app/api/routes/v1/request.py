"""
API routes for data exchange in the Food Department Adapter.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy import select, insert
import json
import uuid
import datetime
from pathlib import Path
import logging

from app.api.dependencies import verify_api_key
from app.services.request_processor import process_request  # Import the function
from app.db.models import SessionLocal, request_tracker
from app.core.config import RESULTS_DIR

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/create")
async def receive_request(request_data: dict, api_key: dict = Depends(verify_api_key)):
    """
    Endpoint to receive requests from Consumer Adapters.
    Validates the request and queues it for processing.
    """
    try:
        # Validate request structure
        if "header" not in request_data or "request_type" not in request_data["header"]:
            raise HTTPException(status_code=400, detail="Invalid request format: missing header or request_type")
        
        # Extract request details
        header = request_data["header"]
        request_id = header.get("request_id", str(uuid.uuid4()))
        request_type = header.get("request_type")
        tenant_id = header.get("tenant_id")
        
        # Validate tenant_id from API key
        if tenant_id != api_key["tenant_id"]:
            raise HTTPException(status_code=403, detail="Tenant ID does not match API key")
        
        # Update request_id if necessary
        if "request_id" not in header:
            request_data["header"]["request_id"] = request_id
        
        # Create a request tracker entry
        session = SessionLocal()
        session.execute(
            request_tracker.insert().values(
                tenant_id=tenant_id,
                request_id=request_id,
                status="pending",
                files=json.dumps([]),
                error=None,
                created_at=datetime.datetime.now(),
                request_payload=request_data  # Save the request payload
            )
        )
        session.commit()
        session.close()
        logger.info(f"Received request {request_id} of type {request_type} for tenant {tenant_id}")
        
        return {
            "header": {
                "request_id": request_id,
                "status": "pending"
            }
        }
    
    except HTTPException as http_exc:
        logger.error(f"HTTPException occurred: {http_exc.detail}")
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{request_id}")
async def get_request_status(request_id: str, api_key: dict = Depends(verify_api_key)):
    """
    Returns the status of a request, including any result files and error messages.
    """
    try:
        # Retrieve status from tracker
        session = SessionLocal()
        status_record = session.execute(
            select(request_tracker).where(
                request_tracker.c.request_id == request_id,
                request_tracker.c.tenant_id == api_key["tenant_id"]
            )
        ).fetchone()
        session.close()
        
        if not status_record:
            raise HTTPException(status_code=404, detail=f"Request ID {request_id} not found")
        
        # Parse files JSON
        files = json.loads(status_record.files) if status_record.files else []
        
        return {
            "header": {
                "request_id": request_id,
                "tenant_id": api_key["tenant_id"],
                "timestamp": datetime.datetime.now().isoformat()
            },
            "body": {
                "status": status_record.status,
                "files": files,
                "error": status_record.error
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/process-requests")
async def get_unprocessed_requests():
    """
    Fetch all unprocessed requests from the request_tracker table and return updated saved request data.
    """
    logger.info("Fetching unprocessed requests from the database")
    try:
        session = SessionLocal()
        unprocessed_requests = session.execute(
            select(request_tracker).where(request_tracker.c.status != "completed")
        ).mappings().all()
        session.close()

        logger.info(f"Fetched {len(unprocessed_requests)} unprocessed requests")
        updated_requests = []

        # Process each unprocessed request
        for request in unprocessed_requests:
            try:
                logger.info(f"Processing request ID: {request['request_id']}")
                await process_request(request)
                logger.info(f"Successfully processed request ID: {request['request_id']}")

                # Fetch updated request data
                session = SessionLocal()
                updated_request = session.execute(
                    select(request_tracker).where(request_tracker.c.request_id == request['request_id'])
                ).mappings().first()
                session.close()

                if updated_request:
                    updated_requests.append(updated_request)
            except Exception as e:
                logger.error(f"Error processing request ID {request['request_id']}: {str(e)}")

        return {
            "status": "success",
            "data": updated_requests
        }
    except Exception as e:
        logger.error(f"Error fetching unprocessed requests: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }