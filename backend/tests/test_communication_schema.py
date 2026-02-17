"""Tests for Communication Book database schema (Task 5.1)."""
import sqlite3
import uuid
import pytest



@pytest.fixture
def db():
    """Provide a fresh in-memory SQLite database with the communication schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create communications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS communications (
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
        )
    """)

    # Create initiator_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS initiator_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            com_id TEXT NOT NULL UNIQUE,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (com_id) REFERENCES communications(com_id)
        )
    """)
    conn.commit()
    yield conn
    conn.close()


def test_communications_table_exists(db):
    """Test that the communications table exists with correct columns."""
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(communications)")
    columns = {row["name"] for row in cursor.fetchall()}
    expected = {
        "com_id", "sender", "recipient", "timestamp",
        "raw_content", "initiator_com_id", "exitor_com_id",
        "is_condensed", "condensed_summary"
    }
    assert expected == columns


def test_initiator_log_table_exists(db):
    """Test that the initiator_log table exists with correct columns."""
    cursor = db.cursor()
    cursor.execute("PRAGMA table_info(initiator_log)")
    columns = {row["name"] for row in cursor.fetchall()}
    assert {"id", "com_id", "timestamp"} == columns


def test_insert_first_message(db):
    """Test inserting the first message in a chain (no initiator_com_id)."""
    cursor = db.cursor()
    com_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
        (com_id, "user", "assistant", "Hello!")
    )
    db.commit()

    cursor.execute("SELECT * FROM communications WHERE com_id = ?", (com_id,))
    row = cursor.fetchone()
    assert row["com_id"] == com_id
    assert row["sender"] == "user"
    assert row["raw_content"] == "Hello!"
    assert row["initiator_com_id"] is None
    assert row["exitor_com_id"] is None
    assert row["is_condensed"] == 0  # SQLite stores BOOLEAN as 0/1


def test_insert_chained_messages(db):
    """Test inserting a chain of two messages with initiator_com_id linking."""
    cursor = db.cursor()
    com_id_1 = str(uuid.uuid4())
    com_id_2 = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
        (com_id_1, "user", "assistant", "First message")
    )
    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content, initiator_com_id) VALUES (?, ?, ?, ?, ?)",
        (com_id_2, "assistant", "user", "Second message", com_id_1)
    )
    db.commit()

    cursor.execute("SELECT * FROM communications WHERE com_id = ?", (com_id_2,))
    row = cursor.fetchone()
    assert row["initiator_com_id"] == com_id_1


def test_update_exitor_com_id(db):
    """Test updating exitor_com_id to form a doubly-linked chain."""
    cursor = db.cursor()
    com_id_1 = str(uuid.uuid4())
    com_id_2 = str(uuid.uuid4())

    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
        (com_id_1, "user", "assistant", "First")
    )
    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content, initiator_com_id) VALUES (?, ?, ?, ?, ?)",
        (com_id_2, "assistant", "user", "Second", com_id_1)
    )
    # Update exitor on first message to point forward
    cursor.execute(
        "UPDATE communications SET exitor_com_id = ? WHERE com_id = ?",
        (com_id_2, com_id_1)
    )
    db.commit()

    cursor.execute("SELECT exitor_com_id FROM communications WHERE com_id = ?", (com_id_1,))
    row = cursor.fetchone()
    assert row["exitor_com_id"] == com_id_2


def test_initiator_log_entry(db):
    """Test that first messages can be recorded in initiator_log."""
    cursor = db.cursor()
    com_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
        (com_id, "user", "assistant", "Start of conversation")
    )
    cursor.execute(
        "INSERT INTO initiator_log (com_id) VALUES (?)",
        (com_id,)
    )
    db.commit()

    cursor.execute("SELECT * FROM initiator_log WHERE com_id = ?", (com_id,))
    row = cursor.fetchone()
    assert row["com_id"] == com_id


def test_com_id_uniqueness(db):
    """Test that duplicate com_ids are rejected."""
    cursor = db.cursor()
    com_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
        (com_id, "user", "assistant", "First")
    )
    db.commit()

    with pytest.raises(Exception):  # Should raise UNIQUE constraint violation
        cursor.execute(
            "INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES (?, ?, ?, ?)",
            (com_id, "user", "assistant", "Duplicate!")
        )
        db.commit()


def test_condensed_message(db):
    """Test storing a condensed message with summary."""
    cursor = db.cursor()
    com_id = str(uuid.uuid4())
    cursor.execute(
        """INSERT INTO communications
           (com_id, sender, recipient, raw_content, is_condensed, condensed_summary)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (com_id, "user", "assistant", "Original long message...", True, "User asked a question")
    )
    db.commit()

    cursor.execute("SELECT * FROM communications WHERE com_id = ?", (com_id,))
    row = cursor.fetchone()
    assert row["is_condensed"] == 1
    assert row["condensed_summary"] == "User asked a question"
