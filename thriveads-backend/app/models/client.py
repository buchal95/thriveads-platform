"""
Client database model
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class Client(Base):
    """Client model for storing client information"""
    
    __tablename__ = "clients"
    
    # Primary key - Meta ad account ID
    id = Column(String, primary_key=True, index=True)
    
    # Client information
    name = Column(String, nullable=False)
    company_name = Column(String)
    email = Column(String)
    
    # Meta API configuration
    meta_ad_account_id = Column(String, nullable=False, unique=True)
    meta_access_token = Column(Text)  # Encrypted in production
    
    # Localization
    language = Column(String, default="cs")  # Czech by default
    country = Column(String, default="CZ")
    currency = Column(String, default="CZK")
    timezone = Column(String, default="Europe/Prague")
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_at = Column(DateTime)
    
    # Relationships will be defined after all models are loaded
    
    def __repr__(self):
        return f"<Client(id={self.id}, name={self.name})>"
