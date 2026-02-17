import sqlite3
import os
from pathlib import Path

# Get the directory of the current file
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the database path
DB_PATH = BASE_DIR / "data" / "messages.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Communications table (blockchain-style message chain)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communications (
                com_id TEXT PRIMARY KEY,             -- UUID v4, generated at save time
                sender TEXT NOT NULL,                -- "user" or "assistant"
                recipient TEXT NOT NULL,             -- "assistant" or "user"
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                raw_content TEXT NOT NULL,           -- Full message text
                initiator_com_id TEXT,               -- com_id of the PREVIOUS message in chain (NULL for first)
                exitor_com_id TEXT,                  -- com_id of the NEXT message in chain (NULL until next is saved)
                is_condensed BOOLEAN DEFAULT FALSE,  -- True if this message has been condensed
                condensed_summary TEXT,              -- Summary text if condensed, else NULL
                FOREIGN KEY (initiator_com_id) REFERENCES communications(com_id),
                FOREIGN KEY (exitor_com_id) REFERENCES communications(com_id)
            )
        """)

        # Initiator log — records the first message of each conversation thread
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS initiator_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                com_id TEXT NOT NULL UNIQUE,         -- References the first communications.com_id
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (com_id) REFERENCES communications(com_id)
            )
        """)

        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
