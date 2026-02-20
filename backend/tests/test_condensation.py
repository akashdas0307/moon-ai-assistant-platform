import unittest
from unittest.mock import AsyncMock, MagicMock
from backend.core.memory.condensation import CondensationEngine
from backend.core.llm.service import LLMService
from backend.core.memory.token_counter import TokenCounter

class TestCondensationEngine(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        # Mock LLMService
        self.mock_llm = MagicMock(spec=LLMService)
        # Mock send_message as async
        self.mock_llm.send_message = AsyncMock()

        # Mock TokenCounter
        self.mock_token_counter = MagicMock(spec=TokenCounter)
        # Default behavior: not needing condensation
        self.mock_token_counter.needs_condensation.return_value = False

        self.engine = CondensationEngine(
            llm_service=self.mock_llm,
            token_counter=self.mock_token_counter
        )

    async def test_no_condensation_when_short(self):
        # Case 1: Small message list -> unchanged
        messages = [{"role": "user", "content": "hi"} for _ in range(5)]
        self.mock_token_counter.needs_condensation.return_value = True # Even if token counter says yes
        # But length is <= 10

        result = await self.engine.condense(messages)
        self.assertEqual(result, messages)
        self.mock_llm.send_message.assert_not_called()

    async def test_no_condensation_when_not_needed(self):
        # Case 2: Token count within budget -> unchanged
        messages = [{"role": "user", "content": "hi"} for _ in range(20)]
        self.mock_token_counter.needs_condensation.return_value = False

        result = await self.engine.condense(messages)
        self.assertEqual(result, messages)
        self.mock_llm.send_message.assert_not_called()

    async def test_edge_case_exactly_10_messages(self):
        # Case 3: 10 messages -> unchanged
        messages = [{"role": "user", "content": str(i)} for i in range(10)]
        self.mock_token_counter.needs_condensation.return_value = True

        result = await self.engine.condense(messages)
        self.assertEqual(result, messages)
        self.mock_llm.send_message.assert_not_called()

    async def test_edge_case_11_messages(self):
        # Case 4: 11 messages -> condense 1 middle message
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(11)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.return_value = "[com_id: 3] summary"

        result = await self.engine.condense(messages)

        # Expected: 3 + 1 + 7 = 11.
        self.assertEqual(len(result), 11)
        self.assertEqual(result[3]["role"], "system")
        self.assertTrue(result[3].get("condensed"))
        self.assertEqual(result[3]["message_count"], 1)

    async def test_condense_structure(self):
        # Case 5: Result has first_3 + 1 condensed + last_7
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(20)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.return_value = "summary"

        result = await self.engine.condense(messages)

        self.assertEqual(len(result), 3 + 1 + 7) # 11 messages total
        self.assertEqual(result[0]["content"], "0")
        self.assertEqual(result[-1]["content"], "19")
        self.assertTrue(result[3].get("condensed"))

    async def test_condense_preserves_first_3(self):
        # Case 6: First 3 messages are identical objects (or at least content)
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(15)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.return_value = "summary"

        result = await self.engine.condense(messages)

        for i in range(3):
            self.assertEqual(result[i], messages[i])

    async def test_condense_preserves_last_7(self):
        # Case 7: Last 7 messages are identical
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(15)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.return_value = "summary"

        result = await self.engine.condense(messages)

        # messages indices: 0..14. Last 7 are 8..14.
        # result indices: 0..2 (first 3), 3 (summary), 4..10 (last 7).

        for i in range(7):
            self.assertEqual(result[4+i], messages[8+i])

    async def test_condensed_block_has_correct_flags(self):
        # Case 8: Correct flags
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(15)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.return_value = "summary"

        result = await self.engine.condense(messages)
        summary_msg = result[3]

        self.assertEqual(summary_msg["role"], "system")
        self.assertTrue(summary_msg["condensed"])
        # Middle count: 15 - 3 - 7 = 5
        self.assertEqual(summary_msg["message_count"], 5)

    async def test_needs_condensation_passthrough(self):
        # Case 9: Passthrough
        self.mock_token_counter.needs_condensation.return_value = True
        self.assertTrue(self.engine.needs_condensation([]))
        self.mock_token_counter.needs_condensation.assert_called_with([])

    async def test_summarise_middle_llm_failure_fallback(self):
        # Case 10: LLM failure
        messages = [{"role": "user", "content": str(i), "com_id": str(i)} for i in range(15)]
        self.mock_token_counter.needs_condensation.return_value = True
        self.mock_llm.send_message.side_effect = Exception("LLM Error")

        result = await self.engine.condense(messages)
        summary_msg = result[3]

        self.assertIn("condensation failed", summary_msg["content"])
        self.assertTrue(summary_msg["condensed"])
        self.assertEqual(summary_msg["message_count"], 5)

if __name__ == "__main__":
    unittest.main()
