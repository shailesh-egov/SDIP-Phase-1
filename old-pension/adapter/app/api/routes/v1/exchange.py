"""
API routes for data exchange with the Food Department system.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select

from app.api.dependencies import verify_api_key
from app.models.schemas import CitizenSearchRequest
from app.services.data_exchange_service import send_request_to_food_service
from app.db.models import SessionLocal, verify_results, search_results

router = APIRouter()

@router.post("/verify")
async def request_food_verify(request_data: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers a verification request to check inclusion errors with the Food Ration system
    """
    try:
        # Set default values if not provided
        if "header" not in request_data:
            request_data["header"] = {
                "request_id": None,
                "request_type": "inclusion",
                "tenant_id": "pension_system",
                "timestamp": None
            }
        else:
            if "request_type" not in request_data["header"]:
                request_data["header"]["request_type"] = "inclusion"
            if "tenant_id" not in request_data["header"]:
                request_data["header"]["tenant_id"] = "pension_system"
        
        # Send request to Food Ration system
        result = await send_request_to_food_service(request_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def request_food_search(request_data: dict, background_tasks: BackgroundTasks, api_key: str = Depends(verify_api_key)):
    """
    Triggers a search request to identify exclusion errors with the Food Ration system
    """
    try:
        # Set default values if not provided
        if "header" not in request_data:
            request_data["header"] = {
                "request_id": None,
                "request_type": "exclusion",
                "tenant_id": "pension_system",
                "timestamp": None
            }
        else:
            if "request_type" not in request_data["header"]:
                request_data["header"]["request_type"] = "exclusion"
            if "tenant_id" not in request_data["header"]:
                request_data["header"]["tenant_id"] = "pension_system"
        
        # Send request to Food Ration system
        result = await send_request_to_food_service(request_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/results")
async def get_citizen_results(search_request: CitizenSearchRequest, api_key: str = Depends(verify_api_key)):
    """
    Retrieves stored results for a citizen by aadhar or other attributes
    """
    try:
        session = SessionLocal()
        results = {}
        
        if search_request.aadhar:
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
            # More complex search based on other attributes
            # This is a simplified example - in a real implementation, you'd need to 
            # decode the JSON columns and search within them
            results = {
                "message": "Searching by attributes other than aadhar is not fully implemented in this example"
            }
        
        session.close()
        return {"status": "success", "data": results}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))