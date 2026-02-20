import pytest
import sqlite3
import uuid
from unittest.mock import patch
from backend.core.communication.service import (
    save_message,
    get_message,
    get_initiators,
    CommunicationCreate,
    Communication
)
from backend.core.communication.service import get_chain, get_full_message, get_conversation_start

class PersistentConnection(sqlite3.Connection):
    """A connection that ignores close() calls to persist state in tests."""
    def close(self):
        pass

    def force_close(self):
        """Actually close the connection."""
        super().close()

@pytest.fixture
def mock_db():
    """In-memory DB with communication schema, injected via monkeypatching."""
    # Use custom factory to prevent closing
    conn = sqlite3.connect(":memory:", factory=PersistentConnection)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # Create tables — copy exact SQL from backend/database/db.py
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

    with patch("backend.core.communication.service.get_db_connection", return_value=conn):
        yield conn

    # Actually close it at the end
    conn.force_close()

def test_save_first_message_generates_com_id(mock_db):
    """save_message() returns a Communication with a non-empty UUID com_id."""
    msg = CommunicationCreate(
        sender="user",
        recipient="assistant",
        raw_content="Hello",
        initiator_com_id=None
    )
    saved = save_message(msg)
    assert isinstance(saved, Communication)
    assert saved.com_id is not None
    assert len(saved.com_id) > 0
    # Basic UUID validation
    assert uuid.UUID(saved.com_id)

def test_save_first_message_logged_to_initiator_log(mock_db):
    """First message (initiator_com_id=None) is recorded in initiator_log."""
    msg = CommunicationCreate(
        sender="user",
        recipient="assistant",
        raw_content="Start conversation",
        initiator_com_id=None
    )
    saved = save_message(msg)

    cursor = mock_db.cursor()
    cursor.execute("SELECT * FROM initiator_log WHERE com_id = ?", (saved.com_id,))
    log_entry = cursor.fetchone()

    assert log_entry is not None
    assert log_entry['com_id'] == saved.com_id

def test_save_second_message_links_to_first(mock_db):
    """Second message's initiator_com_id matches the first message's com_id."""
    # First message
    msg1 = CommunicationCreate(sender="user", recipient="assistant", raw_content="Hi", initiator_com_id=None)
    saved1 = save_message(msg1)

    # Second message
    msg2 = CommunicationCreate(sender="assistant", recipient="user", raw_content="Hello", initiator_com_id=saved1.com_id)
    saved2 = save_message(msg2)

    assert saved2.initiator_com_id == saved1.com_id

def test_save_second_message_backfills_exitor(mock_db):
    """After saving second message, the first message's exitor_com_id is updated to point to second."""
    msg1 = CommunicationCreate(sender="user", recipient="assistant", raw_content="Hi", initiator_com_id=None)
    saved1 = save_message(msg1)

    msg2 = CommunicationCreate(sender="assistant", recipient="user", raw_content="Hello", initiator_com_id=saved1.com_id)
    saved2 = save_message(msg2)

    # Refresh saved1 from DB
    refreshed1 = get_message(saved1.com_id)
    assert refreshed1.exitor_com_id == saved2.com_id

def test_chain_of_three_messages(mock_db):
    """Three chained messages form a complete doubly-linked chain (all forward and back links correct)."""
    # 1 -> 2 -> 3
    msg1 = CommunicationCreate(sender="user", recipient="assistant", raw_content="1", initiator_com_id=None)
    s1 = save_message(msg1)

    msg2 = CommunicationCreate(sender="assistant", recipient="user", raw_content="2", initiator_com_id=s1.com_id)
    s2 = save_message(msg2)

    msg3 = CommunicationCreate(sender="user", recipient="assistant", raw_content="3", initiator_com_id=s2.com_id)
    s3 = save_message(msg3)

    # Refresh from DB
    r1 = get_message(s1.com_id)
    r2 = get_message(s2.com_id)
    r3 = get_message(s3.com_id)

    # Verify links
    assert r1.initiator_com_id is None
    assert r1.exitor_com_id == r2.com_id

    assert r2.initiator_com_id == r1.com_id
    assert r2.exitor_com_id == r3.com_id

    assert r3.initiator_com_id == r2.com_id
    assert r3.exitor_com_id is None

def test_get_message_returns_correct_row(mock_db):
    """get_message(com_id) returns the correct Communication object."""
    msg = CommunicationCreate(sender="user", recipient="assistant", raw_content="Test content", initiator_com_id=None)
    saved = save_message(msg)

    fetched = get_message(saved.com_id)
    assert fetched.com_id == saved.com_id
    assert fetched.raw_content == "Test content"
    assert fetched.sender == "user"

def test_get_message_returns_none_for_missing(mock_db):
    """get_message() returns None for a com_id that doesn't exist."""
    assert get_message("non-existent-id") is None

def test_get_initiators_returns_all_starters(mock_db):
    """get_initiators() returns one entry per conversation start, not mid-chain messages."""
    # Start two conversations
    c1_start = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="C1 start", initiator_com_id=None))
    c2_start = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="C2 start", initiator_com_id=None))

    # Add a reply to C1
    save_message(CommunicationCreate(sender="a", recipient="u", raw_content="C1 reply", initiator_com_id=c1_start.com_id))

    initiators = get_initiators()

    # Should only have the two starters
    assert len(initiators) == 2
    com_ids = [i.com_id for i in initiators]
    assert c1_start.com_id in com_ids
    assert c2_start.com_id in com_ids

    # Verify ordering (most recent first)
    # Since C2 was created after C1, it should be first
    assert initiators[0].com_id == c2_start.com_id
    assert initiators[1].com_id == c1_start.com_id

def test_non_first_message_not_in_initiator_log(mock_db):
    """A chained message (initiator_com_id set) is NOT added to initiator_log."""
    start = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="Start", initiator_com_id=None))
    reply = save_message(CommunicationCreate(sender="a", recipient="u", raw_content="Reply", initiator_com_id=start.com_id))

    cursor = mock_db.cursor()
    cursor.execute("SELECT * FROM initiator_log WHERE com_id = ?", (reply.com_id,))
    assert cursor.fetchone() is None

# --- Task 5.3: Chain Traversal Tests ---

def test_get_chain_single_message(mock_db):
    """Returns a single-message list when the chain has only one message."""
    msg = CommunicationCreate(sender="u", recipient="a", raw_content="Single", initiator_com_id=None)
    saved = save_message(msg)

    chain = get_chain(saved.com_id)
    assert len(chain) == 1
    assert chain[0].com_id == saved.com_id

def test_get_chain_three_messages_from_middle(mock_db):
    """Returns all messages in correct order for a 3-message chain, given the middle com_id."""
    # 1 -> 2 -> 3
    m1 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="1", initiator_com_id=None))
    m2 = save_message(CommunicationCreate(sender="a", recipient="u", raw_content="2", initiator_com_id=m1.com_id))
    m3 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="3", initiator_com_id=m2.com_id))

    chain = get_chain(m2.com_id)
    assert len(chain) == 3
    assert chain[0].com_id == m1.com_id
    assert chain[1].com_id == m2.com_id
    assert chain[2].com_id == m3.com_id

def test_get_chain_three_messages_from_end(mock_db):
    """Returns all messages in correct order when given the last com_id."""
    # 1 -> 2 -> 3
    m1 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="1", initiator_com_id=None))
    m2 = save_message(CommunicationCreate(sender="a", recipient="u", raw_content="2", initiator_com_id=m1.com_id))
    m3 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="3", initiator_com_id=m2.com_id))

    chain = get_chain(m3.com_id)
    assert len(chain) == 3
    assert chain[0].com_id == m1.com_id
    assert chain[1].com_id == m2.com_id
    assert chain[2].com_id == m3.com_id

def test_get_chain_non_existent(mock_db):
    """Returns empty list for a non-existent com_id."""
    chain = get_chain("fake-id")
    assert chain == []

def test_get_full_message_existing(mock_db):
    """Returns the correct raw_content string for an existing message."""
    msg = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="Hello World", initiator_com_id=None))
    content = get_full_message(msg.com_id)
    assert content == "Hello World"

def test_get_full_message_missing(mock_db):
    """Returns None for a non-existent com_id."""
    assert get_full_message("fake-id") is None

def test_get_conversation_start_is_start(mock_db):
    """Returns the message itself when it IS the conversation start."""
    m1 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="Start", initiator_com_id=None))
    start = get_conversation_start(m1.com_id)
    assert start.com_id == m1.com_id
    assert start.initiator_com_id is None

def test_get_conversation_start_from_end(mock_db):
    """Returns the correct start message when given the last message in a 3-message chain."""
    # 1 -> 2 -> 3
    m1 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="1", initiator_com_id=None))
    m2 = save_message(CommunicationCreate(sender="a", recipient="u", raw_content="2", initiator_com_id=m1.com_id))
    m3 = save_message(CommunicationCreate(sender="u", recipient="a", raw_content="3", initiator_com_id=m2.com_id))

    start = get_conversation_start(m3.com_id)
    assert start.com_id == m1.com_id

def test_get_conversation_start_missing(mock_db):
    """Returns None for a non-existent com_id."""
    assert get_conversation_start("fake-id") is None
