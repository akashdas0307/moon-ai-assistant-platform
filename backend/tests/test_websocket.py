"""Tests for WebSocket functionality."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)

@pytest.mark.timeout(30)
def test_websocket_connection(client):
    """Test WebSocket connection and agent integration (streaming)."""
    # Mock the HeadAgent.process_message to return an async generator
    async def mock_streaming_response(content):
        yield "Mocked "
        yield "AI "
        yield "Response"

    with patch("backend.core.agent.head_agent.HeadAgent.process_message", side_effect=mock_streaming_response):

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

            # Should receive stream_start
            start_msg = websocket.receive_json()
            assert start_msg["type"] == "stream_start"
            assert "message_id" in start_msg
            msg_id = start_msg["message_id"]

            # Receive tokens
            t1 = websocket.receive_json()
            assert t1["type"] == "stream_token"
            assert t1["message_id"] == msg_id
            assert t1["token"] == "Mocked "

            t2 = websocket.receive_json()
            assert t2["type"] == "stream_token"
            assert t2["token"] == "AI "

            t3 = websocket.receive_json()
            assert t3["type"] == "stream_token"
            assert t3["token"] == "Response"

            # Should receive stream_end
            end_msg = websocket.receive_json()
            assert end_msg["type"] == "stream_end"
            assert end_msg["message_id"] == msg_id
            assert end_msg["sender"] == "assistant"
            assert end_msg["content"] == "Mocked AI Response"

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
