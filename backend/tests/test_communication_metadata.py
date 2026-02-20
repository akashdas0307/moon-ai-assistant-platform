import pytest
import sqlite3
import uuid
import os
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.communication.service import save_message, get_chain, get_message
from backend.models.communication import CommunicationCreate
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
from backend.api.websocket.handlers import handle_websocket
from backend.database.db import init_db

# --- Fixtures for Service Tests ---

@pytest.fixture
def mock_db_connection(tmp_path, monkeypatch):
    """
    Creates a temporary SQLite database and patches get_db_connection
    in both the database module and the service module.
    """
    db_file = tmp_path / "test_messages.db"

    def _get_connection():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        return conn

    # Patch in database module (for init_db)
    monkeypatch.setattr("backend.database.db.get_db_connection", _get_connection)

    # Patch in service module (where it's used)
    monkeypatch.setattr("backend.core.communication.service.get_db_connection", _get_connection)

    # Initialize the DB schema
    init_db()

    return _get_connection

# --- Service Layer Tests (1-3) ---

def test_save_user_message_generates_com_id(mock_db_connection):
    """Test that saving a user message generates a valid com_id."""
    msg = CommunicationCreate(
        sender="user",
        recipient="assistant",
        raw_content="Hello",
        initiator_com_id=None
    )
    saved = save_message(msg)
    assert saved.com_id is not None
    assert isinstance(uuid.UUID(saved.com_id), uuid.UUID)
    assert saved.initiator_com_id is None

def test_save_ai_message_chains_to_user(mock_db_connection):
    """Test that an AI message correctly chains to the user message."""
    # 1. User message
    user_msg = CommunicationCreate(
        sender="user",
        recipient="assistant",
        raw_content="Hello AI",
        initiator_com_id=None
    )
    saved_user = save_message(user_msg)
    user_com_id = str(saved_user.com_id)

    # 2. AI message chaining to user
    ai_msg = CommunicationCreate(
        sender="assistant",
        recipient="user",
        raw_content="Hello User",
        initiator_com_id=user_com_id
    )
    saved_ai = save_message(ai_msg)

    assert saved_ai.initiator_com_id == saved_user.com_id

    # Verify user message updated with exitor
    refetched_user = get_message(user_com_id)
    assert refetched_user.exitor_com_id == saved_ai.com_id

def test_chain_links_across_turns(mock_db_connection):
    """Test a multi-turn conversation chain."""
    # Turn 1: User -> AI
    u1 = save_message(CommunicationCreate(sender="user", recipient="assistant", raw_content="Hi", initiator_com_id=None))
    a1 = save_message(CommunicationCreate(sender="assistant", recipient="user", raw_content="Hello", initiator_com_id=str(u1.com_id)))

    # Turn 2: User -> AI
    u2 = save_message(CommunicationCreate(sender="user", recipient="assistant", raw_content="How are you?", initiator_com_id=str(a1.com_id)))
    a2 = save_message(CommunicationCreate(sender="assistant", recipient="user", raw_content="Good", initiator_com_id=str(u2.com_id)))

    # Verify chain from end
    chain = get_chain(str(a2.com_id))

    # Chain should be u1 -> a1 -> u2 -> a2
    assert len(chain) == 4
    assert chain[0].com_id == u1.com_id
    assert chain[1].com_id == a1.com_id
    assert chain[2].com_id == u2.com_id
    assert chain[3].com_id == a2.com_id


# --- WebSocket Handler Tests (4-5) ---

# We need a minimal app to mount the websocket handler
app = FastAPI()
@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await handle_websocket(websocket)

client = TestClient(app)

@patch("backend.api.websocket.handlers.save_message")
@patch("backend.api.websocket.handlers.head_agent")
def test_save_message_failure_does_not_break_chat(mock_agent, mock_save):
    """Test that chat continues even if save_message fails."""
    # Mock save_message to raise exception
    mock_save.side_effect = Exception("DB Error")

    # Mock agent to return a generator
    async def token_generator(content):
        yield "Response"
    mock_agent.process_message.return_value = token_generator("test")

    with client.websocket_connect("/ws") as websocket:
        # Receive welcome
        data = websocket.receive_json()
        assert data["type"] == "connection"

        # Send message
        websocket.send_json({"content": "Hello", "last_com_id": None})

        # Expect stream start (even if save failed)
        start = websocket.receive_json()
        assert start["type"] == "stream_start"
        assert start.get("user_com_id") is None

        # Expect tokens
        token = websocket.receive_json()
        assert token["type"] == "stream_token"

        # Expect stream end
        end = websocket.receive_json()
        assert end["type"] == "stream_end"
        assert end.get("ai_com_id") is None

@patch("backend.api.websocket.handlers.save_message")
@patch("backend.api.websocket.handlers.head_agent")
def test_ws_payload_includes_com_ids(mock_agent, mock_save):
    """Test that stream_start and stream_end include com_ids."""

    # Mock user save
    user_uuid = uuid.uuid4()
    mock_user_comm = MagicMock()
    mock_user_comm.com_id = user_uuid

    # Mock AI save
    ai_uuid = uuid.uuid4()
    mock_ai_comm = MagicMock()
    mock_ai_comm.com_id = ai_uuid

    # side_effect to return different values for sequential calls
    mock_save.side_effect = [mock_user_comm, mock_ai_comm]

    # Mock agent
    async def token_generator(content):
        yield "Response"
    mock_agent.process_message.return_value = token_generator("test")

    with client.websocket_connect("/ws") as websocket:
        websocket.receive_json() # Welcome

        # Send message
        last_id = str(uuid.uuid4())
        websocket.send_json({"content": "Hello", "last_com_id": last_id})

        # Check stream_start
        start = websocket.receive_json()
        assert start["type"] == "stream_start"
        assert start["user_com_id"] == str(user_uuid)

        # Check tokens
        token = websocket.receive_json()
        assert token["type"] == "stream_token"

        # Check stream_end
        end = websocket.receive_json()
        assert end["type"] == "stream_end"
        assert end["ai_com_id"] == str(ai_uuid)

        # Verify save_message called with correct args
        assert mock_save.call_count == 2

        # Check first call (User)
        args, _ = mock_save.call_args_list[0]
        assert args[0].sender == "user"
        assert args[0].initiator_com_id == last_id

        # Check second call (AI)
        args, _ = mock_save.call_args_list[1]
        assert args[0].sender == "assistant"
        assert str(args[0].initiator_com_id) == str(user_uuid)
