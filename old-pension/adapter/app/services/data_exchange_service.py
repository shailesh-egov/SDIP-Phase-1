"""
Service for handling data exchange with the Food Department system.
"""
import httpx
import json
import uuid
import datetime
import asyncio
import hashlib
from sqlalchemy import select

from app.core.config import API_KEY, FOOD_SERVICE_URL
from app.db.models import SessionLocal, batch_tracker, verify_results, search_results

async def send_request_to_food_service(request_data):
    """
    Sends a request to the Food Ration system's /food/request endpoint
    """
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
                            status="pending"
                        )
                    )
                    session.commit()
                
                # Start a background task to poll for results
                asyncio.create_task(poll_food_service_results(request_id))
                
                return {
                    "header": {
                        "request_id": request_id,
                        "status": "queued"
                    }
                }
            else:
                print(f"Error sending request to Food Service: {response.text}")
                return {
                    "header": {
                        "status": "error",
                        "message": f"Error communicating with Food Service: {response.status_code}"
                    }
                }
    except Exception as e:
        print(f"Error in send_request_to_food_service: {str(e)}")
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
    try:
        # Initialize status
        status = "pending"
        retries = 0
        max_retries = 30  # Try for about 30 minutes
        
        while status in ["pending", "processing"] and retries < max_retries:
            await asyncio.sleep(60)  # Wait 60 seconds between polls
            retries += 1
            
            # Check status
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{FOOD_SERVICE_URL}/status/{request_id}",
                    headers={"X-API-Key": API_KEY},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data["body"]["status"]
                    
                    if status == "completed":
                        # Fetch results
                        files = status_data["body"]["files"]
                        for file_path in files:
                            part = file_path.split("/")[-1].split(".")[0]
                            result_response = await client.get(
                                f"{FOOD_SERVICE_URL}/results/{request_id}/{part}.json",
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
                        break
                    
                    elif status == "failed":
                        # Update batch status
                        error = status_data["body"].get("error", "Unknown error")
                        with SessionLocal() as session:
                            session.execute(
                                batch_tracker.update()
                                .where(batch_tracker.c.request_id == request_id)
                                .values(status=f"failed: {error}")
                            )
                            session.commit()
                        break
    except Exception as e:
        print(f"Error in poll_food_service_results: {str(e)}")
        
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
    try:
        # Commenting out the business logic for debugging later
        # with SessionLocal() as session:
        #     request_id = result_data["header"]["request_id"]
        #     request_type = result_data["header"]["request_type"]
        #     if request_type == "inclusion":
        #         for result in result_data["body"]["results"]:
        #             aadhar = f"PROB_{hashlib.sha256((result.get('name') + '_' + str(result.get('age')) + '_' + result.get('gender')).encode()).hexdigest()}"
        #             session.execute(
        #                 verify_results.insert().values(
        #                     aadhar=aadhar,
        #                     request_id=request_id,
        #                     criteria_results=result.get("criteria_results", {}),
        #                     match_score=result.get("match_score", 0.0),
        #                     stored_at=datetime.datetime.now()
        #                 )
        #             )
        #     elif request_type == "exclusion":
        #         for citizen in result_data["body"]["citizens"]:
        #             aadhar = citizen.get("aadhar", "")
        #             if not aadhar and "name" in citizen:
        #                 aadhar = f"PROB_{hashlib.sha256(f'{citizen.get('name')}_{citizen.get('age')}_{citizen.get('gender')}'.encode()).hexdigest()}"
        #             session.execute(
        #                 search_results.insert().values(
        #                     aadhar=aadhar,
        #                     request_id=request_id,
        #                     citizen_data=citizen,
        #                     stored_at=datetime.datetime.now()
        #                 )
        #             )
        #     session.commit()
        pass
    except Exception as e:
        print(f"Error in store_results: {str(e)}")