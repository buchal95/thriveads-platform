"""
Database connection and session management
"""

from app.core.database import SessionLocal, engine, Base

# Re-export the database components for compatibility
__all__ = ["SessionLocal", "engine", "Base", "get_db"]


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
