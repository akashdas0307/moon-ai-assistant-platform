import tiktoken
import logging
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

class TokenCounter:
    """
    Class: TokenCounter
    Purpose: Count tokens and manage context budget for the agent think loop.
    """

    def __init__(self, model: str = "gpt-4o", context_limit: int = 128_000):
        """
        Initialize the TokenCounter with a specific model and context limit.

        Args:
            model (str): The model name used for tiktoken encoding selection.
            context_limit (int): Total context window size in tokens.
        """
        self.model = model
        self.context_limit = context_limit

        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            logger.warning(f"Model '{model}' not found in tiktoken. Falling back to 'cl100k_base'.")
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a plain text string."""
        return len(self.encoding.encode(text))

    def count_messages_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Count total tokens for a list of OpenAI-format message dicts.
        Each message has 'role' and 'content'.
        Add 4 tokens per message for the role/formatting overhead
        (standard OpenAI token accounting).
        Add 2 tokens for the reply priming at the end.
        """
        num_tokens = 0
        for message in messages:
            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
            for key, value in message.items():
                if key == "content":
                    num_tokens += self.count_tokens(str(value))
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

    def get_budget(self) -> Dict[str, int]:
        """
        Return the full token budget breakdown as a dict:
        {
            "context_limit": int,          # total context window
            "history_ceiling": int,         # 40% of context_limit — max tokens for conversation history
            "system_ceiling": int,          # 30% of context_limit — soft limit for system prompt
            "response_reserve": int,        # 20% of context_limit — reserved for AI response generation
            "available_for_history": int,   # history_ceiling (no usage tracked yet — context for 6.2)
        }
        """
        return {
            "context_limit": self.context_limit,
            "history_ceiling": int(self.context_limit * 0.4),
            "system_ceiling": int(self.context_limit * 0.3),
            "response_reserve": int(self.context_limit * 0.2),
            "available_for_history": int(self.context_limit * 0.4),
        }

    def measure_system_prompt(self, system_prompt: str) -> Dict[str, Any]:
        """
        Measure the token cost of the assembled system prompt.
        Returns:
        {
            "token_count": int,
            "ceiling": int,          # system_ceiling from get_budget()
            "within_budget": bool,   # True if token_count <= ceiling
            "overage": int,          # tokens over ceiling (0 if within budget)
        }
        """
        token_count = self.count_tokens(system_prompt)
        budget = self.get_budget()
        ceiling = budget["system_ceiling"]
        overage = max(0, token_count - ceiling)

        return {
            "token_count": token_count,
            "ceiling": ceiling,
            "within_budget": token_count <= ceiling,
            "overage": overage,
        }

    def measure_history(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Measure the token cost of the conversation history message list.
        Returns:
        {
            "token_count": int,
            "ceiling": int,          # history_ceiling from get_budget()
            "within_budget": bool,
            "overage": int,
            "message_count": int,
        }
        """
        token_count = self.count_messages_tokens(messages)
        budget = self.get_budget()
        ceiling = budget["history_ceiling"]
        overage = max(0, token_count - ceiling)

        return {
            "token_count": token_count,
            "ceiling": ceiling,
            "within_budget": token_count <= ceiling,
            "overage": overage,
            "message_count": len(messages),
        }

    def needs_condensation(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Returns True if the conversation history token count exceeds
        the history_ceiling (40% of context_limit).
        This is the trigger check that Task 6.2 will call.
        """
        measure = self.measure_history(messages)
        return not measure["within_budget"]

# Default singleton — uses gpt-4o encoding, 128k context window
token_counter = TokenCounter()
