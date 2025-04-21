"""
Service for handling data exchange with the Food Department system.
"""
import httpx
import json
import uuid
import datetime
import asyncio
import hashlib
import logging
from sqlalchemy import select

from app.core.config import API_KEY, FOOD_SERVICE_URL
from app.db.models import SessionLocal, batch_tracker, verify_results, search_results

logger = logging.getLogger(__name__)

async def send_request_to_food_service(request_data):
    """
    Sends a request to the Food Ration system's /food/request endpoint
    """
    logger.info("Starting send_request_to_food_service")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FOOD_SERVICE_URL}/food/request",
                json=request_data,
                headers={"X-API-Key": API_KEY},
                timeout=30.0  # 30 second timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                request_id = response_data["header"]["request_id"]
                
                # Track the batch
                with SessionLocal() as session:
                    batch_id = str(uuid.uuid4())
                    session.execute(
                        batch_tracker.insert().values(
                            batch_id=batch_id,
                            request_id=request_id,
                            last_aadhar="",  # Will be populated during processing
                            last_run=datetime.datetime.now(),
                            status="pending",
                            request_payload=json.dumps(request_data)  # Store the request payload
                        )
                    )
                    session.commit()
                
                logger.info(f"Request {request_id} queued successfully")
                return {
                    "header": {
                        "request_id": request_id,
                        "status": "queued"
                    }
                }
            else:
                logger.error(f"Error sending request to Food Service: {response.text}")
                return {
                    "header": {
                        "status": "error",
                        "message": f"Error communicating with Food Service: {response.status_code}"
                    }
                }
    except Exception as e:
        logger.error(f"Error in send_request_to_food_service: {str(e)}")
        return {
            "header": {
                "status": "error",
                "message": f"Error sending request: {str(e)}"
            }
        }

async def poll_food_service_results(request_id):
    """
    Polls the Food Ration system for results of a request
    """
    logger.info(f"Starting poll_food_service_results for request_id: {request_id}")
    try:
        # Check status
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{FOOD_SERVICE_URL}/food/status/{request_id}",
                headers={"X-API-Key": API_KEY},
                timeout=10.0
            )
            
            if response.status_code == 200:
                status_data = response.json()
                status = status_data["body"]["status"]
                
                if status == "completed":
                    logger.info(f"Request {request_id} completed successfully")
                    # Fetch results
                    files = status_data["body"]["files"]
                    for file_path in files:
                        part = file_path.split("/")[-1].split(".")[0]
                        result_response = await client.get(
                            f"{FOOD_SERVICE_URL}/food/results/{request_id}/{part}.json",
                            headers={"X-API-Key": API_KEY},
                            timeout=30.0
                        )
                        
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            store_results(result_data)
                    
                    # Update batch status
                    with SessionLocal() as session:
                        session.execute(
                            batch_tracker.update()
                            .where(batch_tracker.c.request_id == request_id)
                            .values(status="completed")
                        )
                        session.commit()
                
                elif status == "failed":
                    error = status_data["body"].get("error", "Unknown error")
                    logger.error(f"Request {request_id} failed with error: {error}")
                    # Update batch status
                    with SessionLocal() as session:
                        session.execute(
                            batch_tracker.update()
                            .where(batch_tracker.c.request_id == request_id)
                            .values(status=f"failed: {error}")
                        )
                        session.commit()
    except Exception as e:
        logger.error(f"Error in poll_food_service_results: {str(e)}")
        
        # Update batch status
        with SessionLocal() as session:
            session.execute(
                batch_tracker.update()
                .where(batch_tracker.c.request_id == request_id)
                .values(status=f"error: {str(e)}")
            )
            session.commit()

def store_results(result_data):
    """
    Stores results from the Food Ration system in the local database
    """
    logger.info("Starting store_results")
    try:
        # Commenting out the business logic for debugging later
        with SessionLocal() as session:
            request_id = result_data["header"]["request_id"]
            request_type = result_data["header"]["request_type"]
            if request_type == "verify":
                for result in result_data["body"]["results"]:
                    aadhar = result.get("aadhar", "")
                    session.execute(
                        verify_results.insert().values(
                            aadhar=aadhar,
                            request_id=request_id,
                            criteria_results=result.get("criteria_results", {}),
                            match_score=result.get("match_score", 0.0),
                            stored_at=datetime.datetime.now()
                        )
                    )
            elif request_type == "search":
                for citizen in result_data["body"]["citizens"]:
                    aadhar = citizen.get("aadhar", "")
                    if not aadhar and "name" in citizen:
                        aadhar = hashlib.md5(citizen["name"].encode()).hexdigest()[:12]
                    session.execute(
                        search_results.insert().values(
                            aadhar=aadhar,
                            request_id=request_id,
                            citizen_data=citizen,
                            stored_at=datetime.datetime.now()
                        )
                    )
            session.commit()
        logger.info("store_results completed successfully")
        pass
    except Exception as e:
        logger.error(f"Error in store_results: {str(e)}")