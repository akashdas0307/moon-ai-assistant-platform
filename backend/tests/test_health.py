import pytest
from httpx import AsyncClient
from backend.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test that health check endpoint returns correct response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "moon-ai-backend"
    assert "version" in data
