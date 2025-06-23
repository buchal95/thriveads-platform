"""
Campaign database model
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Campaign(Base):
    """Campaign model for storing campaign information"""
    
    __tablename__ = "campaigns"
    
    # Primary key - Meta campaign ID
    id = Column(String, primary_key=True, index=True)
    
    # Campaign information
    name = Column(String, nullable=False)
    status = Column(String)  # ACTIVE, PAUSED, etc.
    objective = Column(String)  # CONVERSIONS, TRAFFIC, etc.
    
    # Relationships
    client_id = Column(String, ForeignKey("clients.id"), nullable=False)
    
    # Budget information
    daily_budget = Column(Numeric(10, 2))
    lifetime_budget = Column(Numeric(10, 2))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (simplified for now)
    # client = relationship("Client")
    # ads = relationship("Ad")
    
    def __repr__(self):
        return f"<Campaign(id={self.id}, name={self.name})>"
