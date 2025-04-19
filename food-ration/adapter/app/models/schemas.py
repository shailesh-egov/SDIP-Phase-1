"""
Pydantic models for the Food Department Adapter.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uuid
import datetime

class Citizen(BaseModel):
    """Citizen model for data exchange"""
    aadhar: Optional[str] = None
    name: str
    age: int
    gender: str
    caste: str
    location: str

class Criterion(BaseModel):
    """Criterion model for filter conditions"""
    field: str
    operator: str
    value: Union[str, int, float]

class RequestHeader(BaseModel):
    """Header for data exchange requests"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_type: str
    tenant_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())

class InclusionRequest(BaseModel):
    """Request model for inclusion error verification"""
    header: RequestHeader
    body: Dict[str, Any]

class ExclusionRequest(BaseModel):
    """Request model for exclusion error identification"""
    header: RequestHeader
    body: Dict[str, Any]

class StatusResponse(BaseModel):
    """Response model for status endpoints"""
    header: Dict[str, Any]
    body: Dict[str, Any]