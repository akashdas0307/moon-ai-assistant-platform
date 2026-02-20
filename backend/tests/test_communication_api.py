import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.communication import CommunicationCreate
from backend.core.communication.service import save_message
import sqlite3
import uuid

@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Setup a temporary database and return a TestClient.
    Monkeypatches get_db_connection to use the temporary DB.
    """
    # Create a temporary database file
    db_file = tmp_path / "test_communication_api.db"

    def mock_get_db_connection():
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        return conn

    # Monkeypatch get_db_connection in both locations where it might be used
    monkeypatch.setattr("backend.core.communication.service.get_db_connection", mock_get_db_connection)
    # Also patch in backend.database.db just in case other modules use it directly
    monkeypatch.setattr("backend.database.db.get_db_connection", mock_get_db_connection)

    # Initialize schema
    conn = mock_get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS communications (
        com_id TEXT PRIMARY KEY,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        raw_content TEXT NOT NULL,
        initiator_com_id TEXT,
        exitor_com_id TEXT,
        is_condensed BOOLEAN DEFAULT FALSE,
        condensed_summary TEXT,
        FOREIGN KEY (initiator_com_id) REFERENCES communications(com_id),
        FOREIGN KEY (exitor_com_id) REFERENCES communications(com_id)
    )""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS initiator_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        com_id TEXT NOT NULL UNIQUE,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (com_id) REFERENCES communications(com_id)
    )""")
    conn.commit()
    conn.close()

    with TestClient(app) as c:
        yield c

    # Cleanup handled by tmp_path automatically

def test_get_initiators_empty(client):
    """Returns empty list when no messages exist."""
    response = client.get("/api/v1/communications/initiators")
    assert response.status_code == 200
    assert response.json() == []

def test_get_initiators_returns_starters(client):
    """After saving a message with initiator_com_id=None, it appears in /initiators."""
    # Save a starter message
    msg = CommunicationCreate(sender="user", recipient="assistant", raw_content="Start", initiator_com_id=None)
    saved = save_message(msg)

    response = client.get("/api/v1/communications/initiators")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["com_id"] == saved.com_id

def test_get_message_success(client):
    """Save a message, fetch it by com_id, verify fields match."""
    msg = CommunicationCreate(sender="user", recipient="assistant", raw_content="Hello", initiator_com_id=None)
    saved = save_message(msg)

    response = client.get(f"/api/v1/communications/{saved.com_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["com_id"] == saved.com_id
    assert data["raw_content"] == "Hello"
    assert data["sender"] == "user"

def test_get_message_not_found(client):
    """Request a random UUID that doesn't exist, expect 404."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/communications/{fake_id}")
    assert response.status_code == 404

def test_get_chain_success(client):
    """Save a 3-message chain (A->B->C), call /chain on B, verify all 3 are returned in order."""
    # A -> B -> C
    msg1 = CommunicationCreate(sender="u", recipient="a", raw_content="A", initiator_com_id=None)
    s1 = save_message(msg1)

    msg2 = CommunicationCreate(sender="a", recipient="u", raw_content="B", initiator_com_id=s1.com_id)
    s2 = save_message(msg2)

    msg3 = CommunicationCreate(sender="u", recipient="a", raw_content="C", initiator_com_id=s2.com_id)
    s3 = save_message(msg3)

    # Request chain for B (s2)
    response = client.get(f"/api/v1/communications/{s2.com_id}/chain")
    assert response.status_code == 200
    chain = response.json()

    assert len(chain) == 3
    assert chain[0]["com_id"] == s1.com_id
    assert chain[1]["com_id"] == s2.com_id
    assert chain[2]["com_id"] == s3.com_id

    # Check contents
    assert chain[0]["raw_content"] == "A"
    assert chain[1]["raw_content"] == "B"
    assert chain[2]["raw_content"] == "C"

def test_get_chain_not_found(client):
    """Request chain for a non-existent com_id, expect 404."""
    fake_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/communications/{fake_id}/chain")
    assert response.status_code == 404
