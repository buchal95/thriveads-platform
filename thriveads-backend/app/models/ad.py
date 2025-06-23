"""
Ad database model
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Ad(Base):
    """Ad model for storing ad information"""
    
    __tablename__ = "ads"
    
    # Primary key - Meta ad ID
    id = Column(String, primary_key=True, index=True)
    
    # Ad information
    name = Column(String, nullable=False)
    status = Column(String)  # ACTIVE, PAUSED, etc.
    
    # Relationships
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    campaign_id = Column(String, ForeignKey("campaigns.id"))
    adset_id = Column(String)
    
    # Creative information
    creative_id = Column(String)
    preview_url = Column(Text)
    facebook_url = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (simplified for now)
    # client = relationship("Client")
    # campaign = relationship("Campaign")
    
    def __repr__(self):
        return f"<Ad(id={self.id}, name={self.name})>"
