"""
API router initialization for the Food Department Adapter.
"""
from fastapi import APIRouter
from app.api.routes.v1 import exchange, ration_cards

api_router = APIRouter()

# Include routers for different endpoints
# api_router.include_router(ration_cards.router, prefix="/api/ration-cards", tags=["ration-cards"])
api_router.include_router(exchange.router, prefix="/food", tags=["data-exchange"])