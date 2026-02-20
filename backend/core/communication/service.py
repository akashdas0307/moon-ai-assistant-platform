"""
Communication Book Service — Task 5.2
Handles saving messages with com_id generation and doubly-linked chain management.
"""
import uuid
import sqlite3
from datetime import datetime
from typing import Optional, List
from backend.database.db import get_db_connection
from backend.models.communication import Communication, CommunicationCreate, InitiatorLog


def parse_timestamp(ts_str: str) -> datetime:
    """Parse timestamp string from SQLite."""
    try:
        # Standard SQLite current_timestamp format
        return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        # Try with milliseconds if present
        try:
             return datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
             # Fallback to ISO format if needed (e.g. from tests)
             return datetime.fromisoformat(ts_str)


def _row_to_communication(row: sqlite3.Row) -> Communication:
    """
    Helper: convert a sqlite3.Row to a Communication Pydantic model.
    Handles timestamp parsing safely.
    """
    return Communication(
        com_id=row['com_id'],
        sender=row['sender'],
        recipient=row['recipient'],
        timestamp=parse_timestamp(row['timestamp']),
        raw_content=row['raw_content'],
        initiator_com_id=row['initiator_com_id'],
        exitor_com_id=row['exitor_com_id'],
        is_condensed=bool(row['is_condensed']),
        condensed_summary=row['condensed_summary']
    )


def save_message(message: CommunicationCreate) -> Communication:
    """
    Save a message to the communications table.
    - Generates a new UUID com_id.
    - Links to the previous message by setting initiator_com_id.
    - Back-fills the previous message's exitor_com_id to point forward.
    - If initiator_com_id is None (first message), logs to initiator_log.
    Returns the saved Communication object.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Generate new UUID
        new_com_id = str(uuid.uuid4())

        # 2. Insert into communications
        cursor.execute(
            """
            INSERT INTO communications (
                com_id, sender, recipient, raw_content, initiator_com_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                new_com_id,
                message.sender,
                message.recipient,
                message.raw_content,
                message.initiator_com_id
            )
        )

        # 3. If initiator_com_id is NOT None: update previous message's exitor_com_id
        if message.initiator_com_id:
            cursor.execute(
                "UPDATE communications SET exitor_com_id = ? WHERE com_id = ?",
                (new_com_id, message.initiator_com_id)
            )

        # 4. If initiator_com_id IS None: insert into initiator_log
        else:
            cursor.execute(
                "INSERT INTO initiator_log (com_id) VALUES (?)",
                (new_com_id,)
            )

        conn.commit()

        # 6. Fetch and return
        cursor.execute("SELECT * FROM communications WHERE com_id = ?", (new_com_id,))
        row = cursor.fetchone()

        if not row:
            raise ValueError(f"Failed to retrieve saved message with com_id {new_com_id}")

        return _row_to_communication(row)

    finally:
        conn.close()


def get_message(com_id: str) -> Optional[Communication]:
    """
    Retrieve a single message by its com_id.
    Returns None if not found.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM communications WHERE com_id = ?", (com_id,))
        row = cursor.fetchone()

        if row:
            return _row_to_communication(row)
        return None
    finally:
        conn.close()


def get_initiators() -> List[InitiatorLog]:
    """
    Return all entries from initiator_log (conversation starters).
    Ordered by timestamp descending (most recent first).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM initiator_log ORDER BY timestamp DESC, id DESC")
        rows = cursor.fetchall()

        initiators = []
        for row in rows:
            initiators.append(InitiatorLog(
                id=row['id'],
                com_id=row['com_id'],
                timestamp=parse_timestamp(row['timestamp'])
            ))
        return initiators
    finally:
        conn.close()
