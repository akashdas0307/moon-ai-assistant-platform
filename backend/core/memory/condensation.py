import logging
from typing import List, Dict, Any, Optional

from backend.core.llm.service import LLMService
from backend.core.memory.token_counter import TokenCounter, token_counter as default_token_counter
from backend.core.memory.condensation_link import mark_condensed

logger = logging.getLogger(__name__)

class CondensationEngine:
    """
    Engine for condensing conversation history when it exceeds token limits.
    Compresses the middle portion of the message list down to one-line summaries.
    """

    def __init__(self, llm_service: LLMService, token_counter: Optional[TokenCounter] = None):
        """
        Initialize the CondensationEngine.

        Args:
            llm_service: Instance of LLMService for making summarisation calls.
            token_counter: Optional TokenCounter instance. Defaults to the module-level singleton.
        """
        self.llm_service = llm_service
        self.token_counter = token_counter if token_counter else default_token_counter

    def needs_condensation(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Check if the conversation history needs condensation.
        Delegates to the token_counter.
        """
        return self.token_counter.needs_condensation(messages)

    async def condense(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Condense the conversation history if needed.

        Logic:
        1. Check needs_condensation(). If False, return unchanged.
        2. If len(messages) <= 10, return unchanged (cannot split effectively).
        3. Keep first 3 (anchors).
        4. Keep last 7 (recent context).
        5. Condense the middle slice using LLM.
        """
        if not self.needs_condensation(messages):
            return messages

        if len(messages) <= 10:
            logger.info("Message count %d <= 10, skipping condensation despite token overage.", len(messages))
            return messages

        # Slicing
        first_3 = messages[:3]
        last_7 = messages[-7:]
        middle = messages[3:-7]

        if not middle:
            # Should be covered by len check, but safe guard
            return messages

        logger.info("Condensing %d middle messages.", len(middle))
        summary_message = await self._summarise_middle(middle)

        # Persist to DB
        self._persist_condensation(middle, summary_message.get("content", ""))

        return first_3 + [summary_message] + last_7

    def _persist_condensation(self, middle_messages: List[Dict[str, Any]], summary_text: str):
        """
        Extract com_ids from middle messages and mark them as condensed in the DB.
        """
        try:
            com_ids = [msg.get("com_id") for msg in middle_messages if msg.get("com_id")]
            if com_ids:
                mark_condensed(com_ids, summary_text)
        except Exception as e:
            logger.error(f"Failed to persist condensation state to DB: {e}")

    async def _summarise_middle(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Call the LLM to compress the middle slice into a single system-role message.
        """
        # Build prompt
        prompt_lines = [
            "Summarise the following conversation messages into concise one-line summaries per message.",
            "Format each line as:",
            "[com_id: <id>] <one-line summary of what was said>",
            "\nMessages to summarise:"
        ]

        for msg in messages:
            com_id = msg.get("com_id", "no-com_id")
            content = msg.get("content", "")
            role = msg.get("role", "unknown")
            prompt_lines.append(f"Role: {role}, ID: {com_id}\nContent: {content}\n---")

        prompt_content = "\n".join(prompt_lines)

        llm_messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that summarizes conversation history. Keep it concise. Preserve the com_id for each message in the format [com_id: <id>]."
            },
            {
                "role": "user",
                "content": prompt_content
            }
        ]

        try:
            # Non-streaming call with cheap model
            summary_text = await self.llm_service.send_message(
                messages=llm_messages,
                model="openai/gpt-4o-mini",
                stream=False
            )

            # Ensure it is a string
            if not isinstance(summary_text, str):
                summary_text = str(summary_text)

        except Exception as e:
            logger.error(f"Condensation LLM call failed: {e}")
            summary_text = "[condensation failed — middle messages omitted]"

        return {
            "role": "system",
            "content": summary_text,
            "condensed": True,
            "message_count": len(messages),
        }
