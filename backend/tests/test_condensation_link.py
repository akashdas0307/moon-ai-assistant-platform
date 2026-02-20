import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sqlite3
import os
import shutil
import tempfile

from backend.core.memory.condensation_link import mark_condensed, recall_message
from backend.core.memory.condensation import CondensationEngine
from backend.core.llm.service import LLMService

class TestCondensationLink(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for the database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_messages.db")

        # Initialize the database schema
        self._init_db()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE communications (
                com_id TEXT PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                raw_content TEXT NOT NULL,
                initiator_com_id TEXT,
                exitor_com_id TEXT,
                is_condensed BOOLEAN DEFAULT FALSE,
                condensed_summary TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def test_mark_condensed_updates_db(self):
        """Verify mark_condensed updates is_condensed and condensed_summary."""
        conn = self._get_db_connection()
        cursor = conn.cursor()

        # Insert test data
        cursor.execute("INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES ('id1', 'user', 'ai', 'msg1')")
        cursor.execute("INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES ('id2', 'ai', 'user', 'msg2')")
        conn.commit()
        conn.close()

        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            count = mark_condensed(["id1", "id2"], "Summary text")

        self.assertEqual(count, 2)

        # Verify DB state
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT is_condensed, condensed_summary FROM communications WHERE com_id IN ('id1', 'id2')")
        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.assertTrue(row["is_condensed"])
            self.assertEqual(row["condensed_summary"], "Summary text")

    def test_mark_condensed_returns_count(self):
        """Verify return value equals number of rows actually updated."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO communications (com_id, sender, recipient, raw_content) VALUES ('id3', 'user', 'ai', 'msg3')")
        conn.commit()
        conn.close()

        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            # Only id3 exists
            count = mark_condensed(["id3", "nonexistent"], "Summary")

        self.assertEqual(count, 1)

    def test_mark_condensed_empty_list(self):
        """Calling with an empty list returns 0, no DB error."""
        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            count = mark_condensed([], "Summary")
        self.assertEqual(count, 0)

    def test_recall_message_found(self):
        """Insert a row, call recall_message(com_id), verify all fields returned correctly."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO communications (com_id, sender, recipient, raw_content, is_condensed, condensed_summary)
            VALUES ('id4', 'user', 'ai', 'msg4', 0, NULL)
        """)
        conn.commit()
        conn.close()

        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            msg = recall_message("id4")

        self.assertIsNotNone(msg)
        self.assertEqual(msg["com_id"], "id4")
        self.assertEqual(msg["raw_content"], "msg4")
        self.assertFalse(msg["is_condensed"])
        self.assertIsNone(msg["condensed_summary"])

    def test_recall_message_not_found(self):
        """Call recall_message('nonexistent-id'), verify returns None."""
        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            msg = recall_message("nonexistent-id")
        self.assertIsNone(msg)

    def test_recall_condensed_message(self):
        """Insert a condensed row, verify recall_message() returns full raw_content AND condensed_summary."""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO communications (com_id, sender, recipient, raw_content, is_condensed, condensed_summary)
            VALUES ('id5', 'ai', 'user', 'original content', 1, 'short summary')
        """)
        conn.commit()
        conn.close()

        with patch("backend.core.memory.condensation_link.get_db_connection", side_effect=self._get_db_connection):
            msg = recall_message("id5")

        self.assertIsNotNone(msg)
        self.assertEqual(msg["raw_content"], "original content")
        self.assertTrue(msg["is_condensed"])
        self.assertEqual(msg["condensed_summary"], "short summary")

class TestCondensationEngineIntegration(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.llm_service = MagicMock(spec=LLMService)
        # Setup async mock for send_message
        self.llm_service.send_message = AsyncMock(return_value="Condensed Summary")

        self.token_counter = MagicMock()
        self.token_counter.needs_condensation.return_value = True

        self.engine = CondensationEngine(self.llm_service, self.token_counter)

    async def test_condense_marks_db(self):
        """Integration-style test: verify mark_condensed was called with correct com_ids."""
        # Create a list of 15 messages (needs > 10 to condense)
        messages = []
        for i in range(15):
            msg = {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"msg{i}",
                "com_id": f"com_id_{i}"
            }
            messages.append(msg)

        # Middle slice is index 3 to -7 (exclusive of -7)
        # Indices: 3, 4, 5, 6, 7
        # Total 15. -7 is index 8. So 3, 4, 5, 6, 7.
        expected_ids = ["com_id_3", "com_id_4", "com_id_5", "com_id_6", "com_id_7"]

        with patch("backend.core.memory.condensation.mark_condensed") as mock_mark:
            result = await self.engine.condense(messages)

            # Verify mark_condensed called
            mock_mark.assert_called_once()
            call_args = mock_mark.call_args
            args, _ = call_args
            called_ids = args[0]
            called_summary = args[1]

            self.assertEqual(called_ids, expected_ids)
            self.assertEqual(called_summary, "Condensed Summary")

            # Verify result structure
            self.assertEqual(len(result), 3 + 1 + 7) # 11 messages
            self.assertTrue(result[3]["condensed"])
