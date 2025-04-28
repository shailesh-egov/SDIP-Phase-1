"""
API router initialization for the Old Pension Adapter.
"""
from fastapi import APIRouter
from app.api.routes.v1 import results, requests

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(results.router, prefix="/results", tags=["results"])
api_router.include_router(requests.router, prefix="/request", tags=["request"])