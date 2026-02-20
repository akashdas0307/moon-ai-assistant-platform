import unittest
from backend.core.memory.token_counter import TokenCounter

class TestTokenCounter(unittest.TestCase):

    def setUp(self):
        # Use a fresh instance for each test
        self.counter = TokenCounter()

    def test_count_tokens_empty_string(self):
        self.assertEqual(self.counter.count_tokens(""), 0)

    def test_count_tokens_basic(self):
        text = "Hello world"
        count = self.counter.count_tokens(text)
        self.assertTrue(count > 0)
        self.assertTrue(count <= len(text)) # tokens usually <= chars

    def test_count_messages_tokens_empty_list(self):
        # Empty list should return 2 (priming)
        self.assertEqual(self.counter.count_messages_tokens([]), 2)

    def test_count_messages_tokens_single_message(self):
        messages = [{"role": "user", "content": "Hello"}]
        # 4 (overhead) + tokens("Hello") + 2 (priming)
        expected = 4 + self.counter.count_tokens("Hello") + 2
        self.assertEqual(self.counter.count_messages_tokens(messages), expected)

    def test_count_messages_tokens_multi(self):
        msg1 = {"role": "user", "content": "Hello"}
        msg2 = {"role": "assistant", "content": "Hi there"}
        messages = [msg1, msg2]

        count1 = self.counter.count_messages_tokens([msg1])
        count2 = self.counter.count_messages_tokens(messages)

        self.assertTrue(count2 > count1)

        # Calculation:
        # msg1: 4 + tokens("Hello")
        # msg2: 4 + tokens("Hi there")
        # priming: 2
        expected = (4 + self.counter.count_tokens("Hello")) +                    (4 + self.counter.count_tokens("Hi there")) + 2
        self.assertEqual(count2, expected)

    def test_get_budget_structure(self):
        budget = self.counter.get_budget()
        expected_keys = {
            "context_limit", "history_ceiling", "system_ceiling",
            "response_reserve", "available_for_history"
        }
        self.assertEqual(set(budget.keys()), expected_keys)
        for val in budget.values():
            self.assertIsInstance(val, int)
            self.assertGreater(val, 0)

    def test_get_budget_proportions(self):
        # Default 128_000
        budget = self.counter.get_budget()
        self.assertEqual(budget["context_limit"], 128_000)
        self.assertEqual(budget["history_ceiling"], int(128_000 * 0.4))
        self.assertEqual(budget["system_ceiling"], int(128_000 * 0.3))
        self.assertEqual(budget["response_reserve"], int(128_000 * 0.2))

    def test_get_budget_custom_limit(self):
        custom_counter = TokenCounter(context_limit=10_000)
        budget = custom_counter.get_budget()
        self.assertEqual(budget["history_ceiling"], 4000)

    def test_measure_system_prompt_within_budget(self):
        res = self.counter.measure_system_prompt("Short prompt")
        self.assertTrue(res["within_budget"])
        self.assertEqual(res["overage"], 0)
        self.assertGreater(res["token_count"], 0)

    def test_measure_system_prompt_over_budget(self):
        # Create a counter with very small budget
        # 10 tokens context -> system_ceiling = 3
        tiny_counter = TokenCounter(context_limit=10)
        long_text = "This is a very long text that will definitely exceed the small budget."
        res = tiny_counter.measure_system_prompt(long_text)

        self.assertFalse(res["within_budget"])
        self.assertGreater(res["overage"], 0)
        self.assertEqual(res["ceiling"], 3)

    def test_measure_history_structure(self):
        res = self.counter.measure_history([{"role": "user", "content": "test"}])
        expected_keys = {"token_count", "ceiling", "within_budget", "overage", "message_count"}
        self.assertEqual(set(res.keys()), expected_keys)

    def test_measure_history_message_count(self):
        messages = [
            {"role": "user", "content": "1"},
            {"role": "assistant", "content": "2"},
            {"role": "user", "content": "3"}
        ]
        res = self.counter.measure_history(messages)
        self.assertEqual(res["message_count"], 3)

    def test_needs_condensation_empty(self):
        self.assertFalse(self.counter.needs_condensation([]))

    def test_needs_condensation_small(self):
        messages = [{"role": "user", "content": "small"}]
        self.assertFalse(self.counter.needs_condensation(messages))

    def test_needs_condensation_triggers(self):
        # context 50 -> history_ceiling = 20
        tiny_counter = TokenCounter(context_limit=50)
        # construct messages that exceed 20 tokens
        # Each message overhead is 4. "content" adds more.
        # "A long message..." will be > 20 tokens.
        messages = [{"role": "user", "content": "A very very very long message to absolutely guarantee that we exceed the budget of twenty tokens easily."}]
        self.assertTrue(tiny_counter.needs_condensation(messages))

    def test_unknown_model_fallback(self):
        # Should not raise
        fallback_counter = TokenCounter(model="unknown-model-xyz")
        # Should work using fallback encoding
        count = fallback_counter.count_tokens("hello")
        self.assertGreater(count, 0)

if __name__ == "__main__":
    unittest.main()
