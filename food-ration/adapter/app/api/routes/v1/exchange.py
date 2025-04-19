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

from app.api.dependencies import verify_api_key
from app.models.schemas import InclusionRequest, ExclusionRequest
from app.db.models import SessionLocal, request_tracker
from app.core.config import RESULTS_DIR

router = APIRouter()

@router.post("/request")
async def receive_request(request_data: dict, background_tasks: BackgroundTasks, api_key: dict = Depends(verify_api_key)):
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
                created_at=datetime.datetime.now()
            )
        )
        session.commit()
        session.close()
        
        # Queue the request for processing
        import pika
        from app.core.config import RABBITMQ_URL
        
        connection_params = pika.URLParameters(RABBITMQ_URL)
        connection = pika.BlockingConnection(connection_params)
        channel = connection.channel()
        
        # Determine queue based on request type
        queue_name = "inclusion_jobs" if request_type == "inclusion" else "exclusion_jobs"
        
        # Publish message
        channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(request_data),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        
        connection.close()
        
        return {
            "header": {
                "request_id": request_id,
                "status": "queued"
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
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
            select([request_tracker]).where(
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

@router.get("/results/{request_id}/{part}.json")
async def get_results(request_id: str, part: str, api_key: dict = Depends(verify_api_key)):
    """
    Returns the results file for a specific request and part.
    """
    try:
        # Check if result file exists
        file_path = RESULTS_DIR / request_id / f"{part}.json"
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Result file {part}.json not found for request {request_id}")
        
        # Verify tenant_id has access to this request
        session = SessionLocal()
        status_record = session.execute(
            select([request_tracker]).where(
                request_tracker.c.request_id == request_id,
                request_tracker.c.tenant_id == api_key["tenant_id"]
            )
        ).fetchone()
        session.close()
        
        if not status_record:
            raise HTTPException(status_code=403, detail="Not authorized to access this request")
        
        # Return the file
        return FileResponse(
            path=str(file_path),
            media_type="application/json",
            filename=f"{part}.json"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))