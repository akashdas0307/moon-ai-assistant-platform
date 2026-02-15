import pytest
from fastapi.testclient import TestClient
from backend.main import app
import sqlite3
import os

TEST_DB_PATH = "backend/data/test_messages_api.db"

@pytest.fixture
def client(monkeypatch):

    def mock_get_db_connection():
        # Ensure dir exists
        os.makedirs(os.path.dirname(TEST_DB_PATH), exist_ok=True)
        conn = sqlite3.connect(TEST_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("backend.services.message_service.get_db_connection", mock_get_db_connection)
    monkeypatch.setattr("backend.database.db.get_db_connection", mock_get_db_connection)

    # Initialize schema
    conn = mock_get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

    with TestClient(app) as c:
        yield c

    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_create_message(client):
    response = client.post("/api/v1/messages", json={"sender": "user", "content": "Hello API"})
    assert response.status_code == 200
    data = response.json()
    assert data["sender"] == "user"
    assert data["content"] == "Hello API"
    assert "id" in data
    assert "timestamp" in data

def test_list_messages(client):
    # Create some messages
    client.post("/api/v1/messages", json={"sender": "user", "content": "Msg 1"})
    client.post("/api/v1/messages", json={"sender": "assistant", "content": "Msg 2"})

    response = client.get("/api/v1/messages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "Msg 1"
    assert data[1]["content"] == "Msg 2"

def test_list_recent_messages(client):
    for i in range(10):
        client.post("/api/v1/messages", json={"sender": "user", "content": f"Msg {i}"})

    response = client.get("/api/v1/messages/recent?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["content"] == "Msg 5"
    assert data[-1]["content"] == "Msg 9"

def test_delete_messages(client):
    client.post("/api/v1/messages", json={"sender": "user", "content": "Msg 1"})

    response = client.delete("/api/v1/messages")
    assert response.status_code == 204

    response = client.get("/api/v1/messages")
    assert len(response.json()) == 0
