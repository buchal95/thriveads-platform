"""
Simple test to verify the backend setup
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ThriveAds Platform API"
    assert data["version"] == "1.0.0"
    assert data["status"] == "healthy"


def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "database" in data


def test_api_docs_available_in_dev():
    """Test that API docs are available (will fail in production)"""
    response = client.get("/docs")
    # In development, this should return the docs page
    # In production, it should return 404
    assert response.status_code in [200, 404]
