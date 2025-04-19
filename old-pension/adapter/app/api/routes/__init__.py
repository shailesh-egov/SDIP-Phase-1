"""
API router initialization for the Old Pension Adapter.
"""
from fastapi import APIRouter
from app.api.routes.v1 import exchange, pensions

api_router = APIRouter()

# Include routers for different endpoints
# api_router.include_router(pensions.router, prefix="/api/pensions", tags=["pensions"])
api_router.include_router(exchange.router, prefix="/request/food", tags=["data-exchange"])