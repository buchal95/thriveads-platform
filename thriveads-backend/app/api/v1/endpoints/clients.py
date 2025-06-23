"""
Client management endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.client import Client, ClientCreate, ClientUpdate
from app.services.client_service import ClientService

router = APIRouter()


@router.get("/", response_model=List[Client])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all clients"""
    client_service = ClientService(db)
    return await client_service.get_clients(skip=skip, limit=limit)


@router.get("/{client_id}", response_model=Client)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db)
):
    """Get client by ID"""
    client_service = ClientService(db)
    client = await client_service.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.post("/", response_model=Client)
async def create_client(
    client: ClientCreate,
    db: Session = Depends(get_db)
):
    """Create new client"""
    client_service = ClientService(db)
    return await client_service.create_client(client)


@router.put("/{client_id}", response_model=Client)
async def update_client(
    client_id: str,
    client_update: ClientUpdate,
    db: Session = Depends(get_db)
):
    """Update client"""
    client_service = ClientService(db)
    client = await client_service.update_client(client_id, client_update)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db)
):
    """Delete client"""
    client_service = ClientService(db)
    success = await client_service.delete_client(client_id)
    if not success:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}
