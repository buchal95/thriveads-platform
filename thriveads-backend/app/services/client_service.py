"""
Client service for managing client data
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate


class ClientService:
    """Service for client operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_clients(self, skip: int = 0, limit: int = 100) -> List[Client]:
        """Get all clients with pagination"""
        return self.db.query(Client).offset(skip).limit(limit).all()
    
    async def get_client(self, client_id: str) -> Optional[Client]:
        """Get client by ID"""
        return self.db.query(Client).filter(Client.id == client_id).first()
    
    async def create_client(self, client_data: ClientCreate) -> Client:
        """Create new client"""
        # Use meta_ad_account_id as the primary key
        client = Client(
            id=client_data.meta_ad_account_id,
            **client_data.dict()
        )
        
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client
    
    async def update_client(self, client_id: str, client_update: ClientUpdate) -> Optional[Client]:
        """Update client"""
        client = await self.get_client(client_id)
        if not client:
            return None
        
        update_data = client_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(client)
        return client
    
    async def delete_client(self, client_id: str) -> bool:
        """Delete client"""
        client = await self.get_client(client_id)
        if not client:
            return False
        
        self.db.delete(client)
        self.db.commit()
        return True
