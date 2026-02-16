"""Tests for WebSocket functionality."""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.mark.timeout(30)
def test_websocket_connection(client):
    """Test WebSocket connection and agent integration."""
    # Mock the HeadAgent.process_message to return a fixed response immediately
    with patch("backend.core.agent.head_agent.HeadAgent.process_message", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = "Mocked AI Response"

        with client.websocket_connect("/ws") as websocket:
            # Should receive connection message
            data = websocket.receive_json()
            assert data["type"] == "connection"
            assert data["status"] == "connected"
            assert "client_id" in data

            # Send a test message
            test_message = {
                "type": "message",
                "content": "Hello Moon-AI!"
            }
            websocket.send_json(test_message)

            # Should receive agent response (not echo)
            response = websocket.receive_json()
            assert response["type"] == "message"
            assert response["sender"] == "assistant"
            assert response["content"] == "Mocked AI Response"
            assert "client_id" in response

@pytest.mark.timeout(30)
def test_websocket_invalid_json(client):
    """Test WebSocket with invalid JSON."""
    with client.websocket_connect("/ws") as websocket:
        # Receive connection message
        websocket.receive_json()

        # Send invalid JSON
        websocket.send_text("not valid json {{{")

        # Should receive error response
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert "Invalid JSON" in response["message"]
