import backend.core.agent.head_agent as ha
import inspect

print(f"traceback in ha: {hasattr(ha, 'traceback')}")
print(f"Dict in ha: {hasattr(ha, 'Dict')}")
print(f"get_recent_messages in ha: {hasattr(ha, 'get_recent_messages')}")
