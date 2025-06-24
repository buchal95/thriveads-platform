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

# Create database engine with Railway-compatible configuration
def get_database_url():
    """Get database URL with proper configuration for Railway"""
    db_url = settings.DATABASE_URL

    # Handle Railway's DATABASE_URL format
    if db_url.startswith("postgresql://"):
        # Railway provides postgresql:// but SQLAlchemy 2.0+ prefers postgresql+psycopg2://
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    logger.info("Database URL configured", url_scheme=db_url.split("://")[0] if "://" in db_url else "unknown")
    return db_url

# Create database engine
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
    echo=settings.ENVIRONMENT == "development"
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
