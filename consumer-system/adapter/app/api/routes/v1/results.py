from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.models import SessionLocal, search_results, verify_results

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

    # Extract and return only the 'citizen_data' field from the results with pagination info
    return {
        "total_records": total_records,
        "records": [result["citizen_data"] for result in results if "citizen_data" in result],
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
    return [dict(result) for result in results]