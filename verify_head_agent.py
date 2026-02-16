import sys
import asyncio
import inspect
from backend.core.agent.head_agent import HeadAgent, get_recent_messages
import traceback
from typing import Dict

print("Imports successful.")

# Check if get_recent_messages is async
print(f"Is get_recent_messages async? {inspect.iscoroutinefunction(get_recent_messages)}")

# Check if traceback is available in head_agent
import backend.core.agent.head_agent as ha
print(f"traceback in head_agent: {'traceback' in dir(ha)}")

# Check if Dict is available in head_agent
print(f"Dict in head_agent: {'Dict' in dir(ha)}")

# Check Message attributes
from backend.models.message import Message
m = Message(id=1, sender="user", content="test", timestamp="2023-01-01")
print(f"Message attributes: sender={m.sender}, content={m.content}")
