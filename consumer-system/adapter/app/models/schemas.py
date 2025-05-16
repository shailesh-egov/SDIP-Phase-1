"""
Pydantic models for the Old Pension Adapter.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import uuid
import datetime

class Citizen(BaseModel):
    """Citizen model for data exchange"""
    aadhar: str
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
    tenant_id: str = "pension_system"
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

class CitizenSearchRequest(BaseModel):
    """Request model for citizen search endpoints"""
    aadhar: Optional[str] = None
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    caste: Optional[str] = None
    location: Optional[str] = None

class RealmRequest(BaseModel):
    realmName: str
    adminEmail: str
    adminUsername:str
    adminPassword: str

class LoginRequest(BaseModel):
    username: str
    password: str