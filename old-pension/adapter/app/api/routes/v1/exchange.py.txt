"""
API routes for data exchange with the Food Department system.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select

from app.api.dependencies import verify_api_key
from app.models.schemas import CitizenSearchRequest
from app.services.data_exchange_service import send_request_to_food_service
from app.db.models import SessionLocal, verify_results, search_results

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter()

@router.post("/verify")
async def request_food_verify(request_data: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers a verification request to check inclusion errors with the Food Ration system
    """
    logger.info("Received request for food verification")
    try:
        # Set default values if not provided
        if "header" not in request_data:
            logger.debug("Header not found in request data, setting default values")
            request_data["header"] = {
                "request_id": None,
                "request_type": "verify",
                "tenant_id": "pension_system",
                "timestamp": None
            }
        else:
            if "request_type" not in request_data["header"]:
                logger.debug("Request type not found in header, setting default value")
                request_data["header"]["request_type"] = "verify"
            if "tenant_id" not in request_data["header"]:
                logger.debug("Tenant ID not found in header, setting default value")
                request_data["header"]["tenant_id"] = "pension_system"
        
        # Send request to Food Ration system
        logger.info("Sending request to Food Ration system")
        result = await send_request_to_food_service(request_data)
        logger.info("Request to Food Ration system successful")
        return result
    except Exception as e:
        logger.error(f"Error in food verification request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
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

@router.post("/results")
async def get_citizen_results(search_request: CitizenSearchRequest, api_key: str = Depends(verify_api_key)):
    """
    Retrieves stored results for a citizen by aadhar or other attributes
    """
    logger.info("Received request to retrieve citizen results")
    try:
        session = SessionLocal()
        results = {}
        
        if search_request.aadhar:
            logger.debug("Searching results by aadhar")
            # Search by aadhar in verify_results
            query = select([verify_results]).where(verify_results.c.aadhar == search_request.aadhar)
            verify_data = session.execute(query).fetchall()
            
            # Search by aadhar in search_results
            query = select([search_results]).where(search_results.c.aadhar == search_request.aadhar)
            search_data = session.execute(query).fetchall()
            
            results = {
                "verify_results": [dict(row) for row in verify_data],
                "search_results": [dict(row) for row in search_data]
            }
        else:
            logger.debug("Searching results by attributes other than aadhar")
            # More complex search based on other attributes
            results = {
                "message": "Searching by attributes other than aadhar is not fully implemented in this example"
            }
        
        session.close()
        logger.info("Citizen results retrieved successfully")
        return {"status": "success", "data": results}
    
    except Exception as e:
        logger.error(f"Error retrieving citizen results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))