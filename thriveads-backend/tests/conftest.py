"""
Test configuration and fixtures
"""

import pytest
import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from app.core.database import Base, get_db
from app.models.client import Client
from app.models.campaign import Campaign
from app.models.ad import Ad
from app.models.metrics import AdMetrics, CampaignMetrics, WeeklyAdMetrics, MonthlyCampaignMetrics
from main import app


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_client():
    """Sample client data for testing."""
    return Client(
        id="513010266454814",
        name="Mimilátky CZ",
        meta_ad_account_id="513010266454814",
        currency="CZK",
        timezone="Europe/Prague",
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_campaign():
    """Sample campaign data for testing."""
    return Campaign(
        id="campaign_123",
        name="Test Campaign",
        client_id="513010266454814",
        status="ACTIVE",
        objective="CONVERSIONS",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_ad():
    """Sample ad data for testing."""
    return Ad(
        id="ad_123",
        name="Test Ad",
        client_id="513010266454814",
        campaign_id="campaign_123",
        adset_id="adset_123",
        status="ACTIVE",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_ad_metrics():
    """Sample ad metrics data for testing."""
    test_date = date.today() - timedelta(days=1)
    return AdMetrics(
        id=f"ad_123_{test_date.strftime('%Y%m%d')}",
        ad_id="ad_123",
        date=test_date,
        impressions=1000,
        clicks=50,
        spend=Decimal("100.00"),
        conversions=5,
        conversion_value=Decimal("500.00"),
        ctr=Decimal("5.0"),
        cpc=Decimal("2.0"),
        cpm=Decimal("100.0"),
        roas=Decimal("5.0"),
        frequency=Decimal("1.2"),
        attribution="default",
        currency="CZK",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def sample_campaign_metrics():
    """Sample campaign metrics data for testing."""
    test_date = date.today() - timedelta(days=1)
    return CampaignMetrics(
        id=f"campaign_123_{test_date.strftime('%Y%m%d')}",
        campaign_id="campaign_123",
        date=test_date,
        impressions=5000,
        clicks=250,
        spend=Decimal("500.00"),
        conversions=25,
        conversion_value=Decimal("2500.00"),
        ctr=Decimal("5.0"),
        cpc=Decimal("2.0"),
        cpm=Decimal("100.0"),
        roas=Decimal("5.0"),
        frequency=Decimal("1.2"),
        attribution="default",
        currency="CZK",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def mock_meta_api_response():
    """Mock Meta API response data."""
    return {
        'data': [
            {
                'ad_id': 'ad_123',
                'ad_name': 'Test Ad',
                'campaign_name': 'Test Campaign',
                'adset_name': 'Test AdSet',
                'impressions': '1000',
                'clicks': '50',
                'spend': '100.00',
                'actions': [
                    {'action_type': 'purchase', 'value': '5'}
                ],
                'action_values': [
                    {'action_type': 'purchase', 'value': '500.00'}
                ],
                'ctr': '5.0',
                'cpc': '2.0',
                'cpm': '100.0',
                'frequency': '1.2',
                'account_currency': 'CZK'
            }
        ]
    }


@pytest.fixture
def mock_facebook_api():
    """Mock Facebook API client."""
    mock_api = Mock()
    mock_api.get_insights = AsyncMock()
    return mock_api


# Test data generators
def generate_daily_metrics(ad_id: str, days: int = 7) -> list:
    """Generate sample daily metrics for testing."""
    metrics = []
    for i in range(days):
        test_date = date.today() - timedelta(days=i+1)
        metrics.append(AdMetrics(
            id=f"{ad_id}_{test_date.strftime('%Y%m%d')}",
            ad_id=ad_id,
            date=test_date,
            impressions=1000 + (i * 100),
            clicks=50 + (i * 5),
            spend=Decimal(str(100 + (i * 10))),
            conversions=5 + i,
            conversion_value=Decimal(str(500 + (i * 50))),
            ctr=Decimal("5.0"),
            cpc=Decimal("2.0"),
            cpm=Decimal("100.0"),
            roas=Decimal("5.0"),
            frequency=Decimal("1.2"),
            attribution="default",
            currency="CZK",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    return metrics


def generate_weekly_metrics(ad_id: str, weeks: int = 4) -> list:
    """Generate sample weekly metrics for testing."""
    metrics = []
    for i in range(weeks):
        week_start = date.today() - timedelta(days=(i+1)*7)
        week_end = week_start + timedelta(days=6)
        metrics.append(WeeklyAdMetrics(
            id=f"{ad_id}_{week_start.strftime('%Y%m%d')}",
            ad_id=ad_id,
            week_start_date=week_start,
            week_end_date=week_end,
            impressions=7000 + (i * 1000),
            clicks=350 + (i * 50),
            spend=Decimal(str(700 + (i * 100))),
            conversions=35 + (i * 5),
            conversion_value=Decimal(str(3500 + (i * 500))),
            ctr=Decimal("5.0"),
            cpc=Decimal("2.0"),
            cpm=Decimal("100.0"),
            roas=Decimal("5.0"),
            frequency=Decimal("1.2"),
            attribution="default",
            currency="CZK",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        ))
    return metrics
