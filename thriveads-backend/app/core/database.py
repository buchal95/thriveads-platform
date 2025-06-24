"""
Database configuration and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import structlog

from .config import settings

logger = structlog.get_logger()

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async engine for async operations (only if needed)
def get_async_engine():
    return create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        pool_pre_ping=True,
        pool_recycle=300,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_async_session_local():
    async_engine = get_async_engine()
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """Dependency to get async database session"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they are registered
        from app.models import client, campaign, ad, metrics
        
        # Create tables
        async_engine = get_async_engine()
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
