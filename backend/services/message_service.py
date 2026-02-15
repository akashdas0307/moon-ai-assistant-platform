from typing import List
from datetime import datetime
from backend.database.db import get_db_connection
from backend.models.message import Message, MessageCreate

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

def save_message(message: MessageCreate) -> Message:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (sender, content) VALUES (?, ?)",
            (message.sender, message.content)
        )
        message_id = cursor.lastrowid
        conn.commit()

        # Retrieve the saved message to get the timestamp
        cursor.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
        row = cursor.fetchone()

        return Message(
            id=row['id'],
            sender=row['sender'],
            content=row['content'],
            timestamp=parse_timestamp(row['timestamp'])
        )
    finally:
        conn.close()

def get_all_messages(limit: int = 100) -> List[Message]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Order by timestamp ASC, id ASC to handle same-second timestamps correctly
        cursor.execute("SELECT * FROM messages ORDER BY timestamp ASC, id ASC LIMIT ?", (limit,))
        rows = cursor.fetchall()

        messages = []
        for row in rows:
            messages.append(Message(
                id=row['id'],
                sender=row['sender'],
                content=row['content'],
                timestamp=parse_timestamp(row['timestamp'])
            ))
        return messages
    finally:
        conn.close()

def get_recent_messages(limit: int = 50) -> List[Message]:
    """Get the most recent messages, ordered chronologically."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Get the last N messages, but we need them in ASC order for chat history
        # Use id as secondary sort key for consistent ordering
        query = """
            SELECT * FROM (
                SELECT * FROM messages ORDER BY timestamp DESC, id DESC LIMIT ?
            ) ORDER BY timestamp ASC, id ASC
        """
        cursor.execute(query, (limit,))
        rows = cursor.fetchall()

        messages = []
        for row in rows:
            messages.append(Message(
                id=row['id'],
                sender=row['sender'],
                content=row['content'],
                timestamp=parse_timestamp(row['timestamp'])
            ))
        return messages
    finally:
        conn.close()

def clear_all_messages() -> int:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        count = cursor.rowcount
        conn.commit()
        return count
    finally:
        conn.close()
