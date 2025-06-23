"""
Ad service for managing ad data
"""

from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.ad import Ad
from app.schemas.ad import AdCreate, AdUpdate


class AdService:
    """Service for ad operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_ad(self, ad_id: str) -> Optional[Ad]:
        """Get ad by ID"""
        return self.db.query(Ad).filter(Ad.id == ad_id).first()
    
    async def get_ads_by_client(self, client_id: str, skip: int = 0, limit: int = 100) -> List[Ad]:
        """Get ads for a specific client"""
        return (
            self.db.query(Ad)
            .filter(Ad.client_id == client_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
