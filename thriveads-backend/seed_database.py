"""
Database seeding script for ThriveAds Platform
Seeds the database with initial client data
"""

import asyncio
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import SessionLocal, engine, Base
from app.models.client import Client
from app.core.config import settings


async def create_tables():
    """Create all database tables"""
    print("Checking database tables...")
    # Tables should already be created by Alembic migration
    print("✅ Database tables ready")


async def seed_clients(db: Session):
    """Seed initial client data"""
    print("Seeding client data...")
    
    # Check if Mimilátky CZ client already exists
    existing_client = db.query(Client).filter(
        Client.meta_ad_account_id == settings.DEFAULT_CLIENT_ID
    ).first()
    
    if existing_client:
        print(f"✅ Client {existing_client.name} already exists")
        return existing_client
    
    # Create Mimilátky CZ client
    mimílatky_client = Client(
        id=settings.DEFAULT_CLIENT_ID,
        name="Mimilátky CZ",
        company_name="Mimilátky s.r.o.",
        email="info@mimilatky.cz",
        meta_ad_account_id=settings.DEFAULT_CLIENT_ID,
        language="cs",
        country="CZ",
        currency="CZK",
        timezone="Europe/Prague",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(mimílatky_client)
    db.commit()
    db.refresh(mimílatky_client)
    
    print(f"✅ Created client: {mimílatky_client.name} (ID: {mimílatky_client.id})")
    return mimílatky_client


async def main():
    """Main seeding function"""
    print("🌱 Starting database seeding...")
    
    # Create tables
    await create_tables()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed clients
        client = await seed_clients(db)
        
        print("\n🎉 Database seeding completed successfully!")
        print(f"📊 Client ready: {client.name}")
        print(f"🔑 Meta Ad Account ID: {client.meta_ad_account_id}")
        print(f"🌍 Language: {client.language}")
        print(f"💰 Currency: {client.currency}")
        
        print("\n📝 Next steps:")
        print("1. Configure Meta API credentials in .env file")
        print("2. Start the FastAPI server: uvicorn main:app --reload")
        print("3. Test the API endpoints at http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
