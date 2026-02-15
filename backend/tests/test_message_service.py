import pytest
import os
import sqlite3
from datetime import datetime
from backend.services.message_service import (
    save_message,
    get_all_messages,
    get_recent_messages,
    clear_all_messages
)
from backend.models.message import MessageCreate

# Use a test database
TEST_DB_PATH = "backend/data/test_messages.db"

@pytest.fixture(autouse=True)
def setup_teardown_db():
    # Override the DB path in the module (if possible) or just rely on env vars if supported.
    # Since we can't easily change the global variable in db.py without reloading,
    # we might need to patch get_db_connection.

    # However, simpler approach:
    # We will backup the real DB if it exists, or just use a separate file and patch.
    pass

@pytest.fixture
def db_connection(monkeypatch):
    """Overrides the database connection to use a test database."""

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

    yield

    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_save_message(db_connection):
    msg = MessageCreate(sender="user", content="Hello")
    saved = save_message(msg)

    assert saved.id is not None
    assert saved.sender == "user"
    assert saved.content == "Hello"
    assert isinstance(saved.timestamp, datetime)

def test_get_all_messages(db_connection):
    save_message(MessageCreate(sender="user", content="Msg 1"))
    save_message(MessageCreate(sender="assistant", content="Msg 2"))

    messages = get_all_messages()
    assert len(messages) == 2
    assert messages[0].content == "Msg 1"
    assert messages[1].content == "Msg 2"

def test_get_recent_messages(db_connection):
    for i in range(10):
        save_message(MessageCreate(sender="user", content=f"Msg {i}"))

    recent = get_recent_messages(limit=5)
    assert len(recent) == 5
    assert recent[0].content == "Msg 5"
    assert recent[-1].content == "Msg 9"

def test_clear_all_messages(db_connection):
    save_message(MessageCreate(sender="user", content="Msg 1"))
    save_message(MessageCreate(sender="assistant", content="Msg 2"))

    count = clear_all_messages()
    assert count == 2

    messages = get_all_messages()
    assert len(messages) == 0
