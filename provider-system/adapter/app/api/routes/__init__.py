"""
API router initialization for the Food Department Adapter.
"""
from fastapi import APIRouter
from app.api.routes.v1 import request, results

api_router = APIRouter()

# Include routers for different endpoints
api_router.include_router(request.router, prefix="/request", tags=["request"])
api_router.include_router(results.router, prefix="/results", tags=["results"])