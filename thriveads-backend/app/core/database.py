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

# Lazy database engine creation
_engine = None
_SessionLocal = None

def get_engine():
    """Get database engine (created lazily)"""
    global _engine
    if _engine is None:
        _engine = create_engine(
            get_database_url(),
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            echo=settings.ENVIRONMENT == "development"
        )
    return _engine

def get_session_local():
    """Get session factory (created lazily)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

# Create async engine for async operations (only if needed)
def get_async_engine():
    return create_async_engine(
        settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
        pool_pre_ping=True,
        pool_recycle=300,
    )

def get_async_session_local():
    async_engine = get_async_engine()
    return sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    SessionLocal = get_session_local()
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

        # Create tables using sync engine for simplicity
        engine = get_engine()
        Base.metadata.create_all(bind=engine)

        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
