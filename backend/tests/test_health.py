from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test the health check endpoint returns 200 and correct data."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data

def test_health_endpoint_structure():
    """Test the health endpoint returns all required fields."""
    response = client.get("/api/v1/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert isinstance(data["timestamp"], str)
