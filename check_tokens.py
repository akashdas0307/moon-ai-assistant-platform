from backend.core.memory.token_counter import TokenCounter
tc = TokenCounter(context_limit=50)
msg = "A long message to exceed the budget of twenty tokens easily."
count = tc.count_tokens(msg)
full_count = tc.count_messages_tokens([{"role": "user", "content": msg}])
print(f"Content tokens: {count}")
print(f"Full tokens: {full_count}")
print(f"Ceiling: {tc.get_budget()['history_ceiling']}")
