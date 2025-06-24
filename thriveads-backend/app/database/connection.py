"""
Database connection and session management
"""

from app.core.database import get_engine, get_session_local, Base, get_db

# Re-export the database components for compatibility
__all__ = ["get_engine", "get_session_local", "Base", "get_db"]

# For backward compatibility, create lazy properties
def SessionLocal():
    """Backward compatibility - returns session factory"""
    return get_session_local()

def engine():
    """Backward compatibility - returns engine"""
    return get_engine()
