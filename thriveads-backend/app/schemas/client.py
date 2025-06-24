"""
Client Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ClientBase(BaseModel):
    """Base client schema"""
    name: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    meta_ad_account_id: str
    language: str = "cs"
    country: str = "CZ"
    currency: str = "CZK"
    timezone: str = "Europe/Prague"


class ClientCreate(ClientBase):
    """Schema for creating a new client"""
    meta_access_token: Optional[str] = None


class ClientUpdate(BaseModel):
    """Schema for updating a client"""
    name: Optional[str] = None
    company_name: Optional[str] = None
    email: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class Client(ClientBase):
    """Full client schema"""
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
