"""Tests for WebSocket functionality."""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
import json


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_websocket_connection(client):
    """Test WebSocket connection and echo."""
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

        # Should receive echo response
        response = websocket.receive_json()
        assert response["type"] == "echo"
        assert response["original_message"] == test_message
        assert "server_message" in response


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
