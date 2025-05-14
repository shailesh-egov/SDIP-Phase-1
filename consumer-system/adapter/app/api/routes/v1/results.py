import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.models import SessionLocal, search_results, verify_results
from app.utils.mask import mask_id_with_hash
from app.utils.key_manager import KeyManager
from app.utils.encryptor import Encryptor
from app.core.config import ENCRYPTION_KEYS, CURRENT_KEY_ID

# Initialize KeyManager and Encryptor
key_manager = KeyManager(ENCRYPTION_KEYS, CURRENT_KEY_ID)
encryptor = Encryptor(key_manager)

logger = logging.getLogger(__name__)

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/search/{request_id}")
async def get_search_results(request_id: str, skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """
    API to fetch search results based on request_id with pagination.
    """
    query = search_results.select().where(search_results.c.request_id == request_id)
    total_records = db.execute(query).rowcount  # Get total number of records

    results = db.execute(
        query.offset(skip).limit(limit)
    ).mappings().fetchall()  # Use .mappings() to get results as dictionaries

    if not results:
        raise HTTPException(status_code=404, detail="Search results not found")

    decrypted_results = []
    for row in results:
        result = dict(row)
        if "citizen_data" in result:
            try:
                result["citizen_data"] = encryptor.decrypt(result["citizen_data"])
            except Exception as e:
                logger.error(f"Failed to decrypt citizen_data: {str(e)}")

        decrypted_results.append(result)


    # Extract and return only the 'citizen_data' field from the results with pagination info
    return {
        "total_records": total_records,
        "records": [dict(result) for result in decrypted_results],
        "pagination": {
            "skip": skip,
            "limit": limit
        }
    }

@router.get("/verify/{request_id}")
async def get_verify_results(request_id: str, db: Session = Depends(get_db)):
    """
    API to fetch verify results based on request_id.
    """
    results = db.execute(
        verify_results.select().where(verify_results.c.request_id == request_id)
    ).mappings().fetchall()  # Use .mappings() to get results as dictionaries

    if not results:
        raise HTTPException(status_code=404, detail="Verify results not found")

    # Convert results to a list of dictionaries
    decrypted_results = []
    for row in results:
        result = dict(row)  # Convert RowMapping to a regular dict so you can modify it
        # result["aadhar"] = aadhar  # add or modify fields safely 

        if "criteria_results" in result:
            try:
                result["criteria_results"] = encryptor.decrypt(result["criteria_results"])
            except Exception as e:
                logger.error(f"Failed to decrypt citizen_data: {e}")
                # result["criteria_results"] = None  # Or handle accordingly

        decrypted_results.append(result)


    return [dict(result) for result in decrypted_results]


@router.get("/search/aadhar/{aadhar}")
async def get_search_results_by_aadhar(aadhar: str, db: Session = Depends(get_db)):
    """
    API to fetch verify results based on request_id.
    """
    if not aadhar.isdigit() or len(aadhar) != 12:
        raise HTTPException(status_code=400, detail="Invalid Aadhar format")

    masked_aadhar = mask_id_with_hash(aadhar)
    results = db.execute(
        search_results.select().where(search_results.c.aadhar == masked_aadhar)
    ).mappings().fetchall()  # Use .mappings() to get results as dictionaries


    if not results:
        raise HTTPException(status_code=404, detail=f"Search results not found for aadhar: {aadhar}")


    decrypted_results = []
    for row in results:
        result = dict(row)  # Convert RowMapping to a regular dict so you can modify it
        result["aadhar"] = aadhar  # add or modify fields safely

        if "citizen_data" in result:
            try:
                result["citizen_data"] = encryptor.decrypt(result["citizen_data"])
            except Exception as e:
                logger.error(f"Failed to decrypt citizen_data: {e}")
                result["citizen_data"] = None  # Or handle accordingly

        decrypted_results.append(result)


    return [dict(result) for result in decrypted_results]




@router.get("/verify/aadhar/{aadhar}")
async def get_verify_results_by_aadhar(aadhar: str, db: Session = Depends(get_db)):
    """
    API to fetch verify results based on request_id.
    """
    if not aadhar.isdigit() or len(aadhar) != 12:
        raise HTTPException(status_code=400, detail="Invalid Aadhar format")

    masked_aadhar = mask_id_with_hash(aadhar)
    results = db.execute(
        verify_results.select().where(verify_results.c.aadhar == masked_aadhar)
    ).mappings().fetchall()  # Use .mappings() to get results as dictionaries

    if not results:
        raise HTTPException(status_code=404, detail=f"Verify results not found for aadhar: {aadhar}")
    
    decrypted_results = []
    for row in results:
        result = dict(row)  # Convert RowMapping to a regular dict so you can modify it
        result["aadhar"] = aadhar  # add or modify fields safely

        if "criteria_results" in result:
            try:
                result["criteria_results"] = encryptor.decrypt(result["criteria_results"])
            except Exception as e:
                logger.error(f"Failed to decrypt citizen_data: {e}")
                result["criteria_results"] = None  # Or handle accordingly

        decrypted_results.append(result)


    return [dict(result) for result in decrypted_results]
