import logging
import uuid  # Import the uuid module to generate unique request IDs
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from app.db.models import SessionLocal, batch_tracker, verify_results, search_results
from app.services.data_exchange_service import poll_food_service_results, send_request_to_food_service
from app.api.dependencies import verify_api_key
from app.models.schemas import CitizenSearchRequest

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    """
    Dependency to provide a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Fetch Pending Requests Route
@router.get("/fetch_pending_requests")
async def fetch_pending_requests():
    """
    API to fetch pending or processing requests from the database and poll their status.
    """
    logger.info("Starting fetch_pending_requests API")
    try:
        with SessionLocal() as session:
            # Fetch requests with status 'pending' or 'processing'
            pending_requests = session.execute(
                select(batch_tracker.c.request_id).where(
                    batch_tracker.c.status.in_(["pending", "processing"])
                )
            ).fetchall()

            for request in pending_requests:
                request_id = request[0]
                await poll_food_service_results(request_id)

        logger.info("Polling completed successfully.")
        return {"status": "success", "message": "Polling completed for pending requests."}
    except Exception as e:
        logger.error(f"Error in fetch_pending_requests: {str(e)}")
        return {"status": "error", "message": f"Error occurred: {str(e)}"}

# Verify Route
@router.post("/food/verify")
async def request_food_verify(request_data: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers a verification request to check inclusion errors with the Food Ration system
    """
    logger.info("Received request for food verification")
    try:
        # Validate request body structure
        if "header" not in request_data or "body" not in request_data:
            raise HTTPException(status_code=400, detail="Request must contain 'header' and 'body' sections.")

        # Validate header
        header = request_data["header"]
        if "request_type" not in header or "tenant_id" not in header:
            raise HTTPException(status_code=400, detail="Header must contain 'request_type' and 'tenant_id'.")
        if header["request_type"] != "verify":
            raise HTTPException(status_code=400, detail="Invalid 'request_type'. It must be 'verify'.")

        # Generate a unique request_id if not provided
        if "request_id" not in header or not header["request_id"]:
            header["request_id"] = str(uuid.uuid4())
            logger.info(f"Generated unique request_id: {header['request_id']}")

        # Validate body
        body = request_data["body"]
        if "citizens" not in body or not isinstance(body["citizens"], list):
            raise HTTPException(status_code=400, detail="Body must contain a 'citizens' array.")
        if "criteria" not in body or not isinstance(body["criteria"], list):
            raise HTTPException(status_code=400, detail="Body must contain a 'criteria' array.")

        # Validate citizens
        for citizen in body["citizens"]:
            if not isinstance(citizen, dict):
                raise HTTPException(status_code=400, detail="Each citizen must be an object.")
            if "aadhar" not in citizen and not all(key in citizen for key in ["name", "gender", "caste"]):
                raise HTTPException(
                    status_code=400,
                    detail="Each citizen must have either 'aadhar' or all of the following fields: 'name', 'gender', 'caste'."
                )

        # Validate criteria
        for criterion in body["criteria"]:
            if not isinstance(criterion, dict):
                raise HTTPException(status_code=400, detail="Each criterion must be an object.")
            if not all(key in criterion for key in ["field", "operator", "value"]):
                raise HTTPException(
                    status_code=400,
                    detail="Each criterion must contain 'field', 'operator', and 'value'."
                )

        # Process the request (e.g., send to Food Ration system)
        logger.info("Sending request to Food Ration system")
        result = await send_request_to_food_service(request_data)
        logger.info("Request to Food Ration system successful")
        return result

    except HTTPException as e:
        logger.error(f"Validation error in food verification request: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"Error in food verification request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Search Route
@router.post("/food/search")
async def request_food_search(request_data: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers a search request to identify exclusion errors with the Food Ration system
    """
    logger.info("Received request for food search")
    try:
        # Set default values if not provided
        if "header" not in request_data:
            logger.debug("Header not found in request data, setting default values")
            request_data["header"] = {
                "request_id": None,
                "request_type": "exclusion",
                "tenant_id": "pension_system",
                "timestamp": None
            }
        else:
            if "request_type" not in request_data["header"]:
                logger.debug("Request type not found in header, setting default value")
                request_data["header"]["request_type"] = "exclusion"
            if "tenant_id" not in request_data["header"]:
                logger.debug("Tenant ID not found in header, setting default value")
                request_data["header"]["tenant_id"] = "pension_system"
        
        # Send request to Food Ration system
        logger.info("Sending request to Food Ration system")
        result = await send_request_to_food_service(request_data)
        logger.info("Request to Food Ration system successful")
        return result
    except Exception as e:
        logger.error(f"Error in food search request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Batch Tracker Requests Route
@router.get("/search")
async def get_batch_requests(
    status: str = None, request_id: str = None, db: Session = Depends(get_db)
):
    """
    API to fetch requests from batch_tracker table with optional filters for status and request_id.
    """
    logger.info("Fetching batch tracker requests with filters")
    try:
        # Build the query dynamically based on filters
        query = select(batch_tracker)
        if status:
            query = query.where(batch_tracker.c.status == status)
        if request_id:
            query = query.where(batch_tracker.c.request_id == request_id)

        # Execute the query
        results = db.execute(query).mappings().fetchall()

        if not results:
            return {"status": "success", "data": [], "message": "No matching records found."}

        # Convert results to a list of dictionaries
        data = [dict(result) for result in results]
        return {"status": "success", "data": data}
    except Exception as e:
        logger.error(f"Error fetching batch tracker requests: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching batch tracker requests")

