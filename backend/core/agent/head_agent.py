"""Head Agent - Main agent think loop for Moon-AI system."""

import logging
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator
import traceback

from backend.core.llm.service import LLMService, llm_service as global_llm_service
from backend.services.message_service import get_recent_messages, save_message
from backend.models.message import MessageCreate

logger = logging.getLogger(__name__)

# Path to agent core files
AGENT_FILES_DIR = Path(__file__).resolve().parent.parent.parent / "agents" / "head-agent"


class HeadAgent:
    """
    Head Agent that manages the central think loop of the Moon-AI system.
    It loads identity files, maintains context, and communicates via LLM.
    """

    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the Head Agent.

        Args:
            llm_service: Optional LLMService instance. If not provided,
                         attempts to use the global instance.
        """
        self.llm_service = llm_service if llm_service else global_llm_service
        self.agent_files_dir = AGENT_FILES_DIR

        if self.llm_service:
            logger.info("HeadAgent initialized with LLM service.")
        else:
            logger.warning("HeadAgent initialized WITHOUT LLM service. AI responses disabled.")

    def _read_file(self, filename: str) -> str:
        """
        Read a file from the agent files directory.

        Args:
            filename: Name of the file to read (e.g., "AGENT.md")

        Returns:
            File content as string, or empty string if not found.
        """
        file_path = self.agent_files_dir / filename
        try:
            if file_path.exists():
                return file_path.read_text(encoding="utf-8")
            else:
                logger.warning(f"Agent file not found: {file_path}")
                return ""
        except Exception as e:
            logger.error(f"Error reading agent file {filename}: {e}")
            return ""

    def _get_notebook_tail(self, num_lines: int = 15) -> str:
        """
        Read the last N lines of NOTEBOOK.md.

        Args:
            num_lines: Number of lines to return from the end.

        Returns:
            String containing the last N lines.
        """
        content = self._read_file("NOTEBOOK.md")
        if not content:
            return ""

        lines = content.splitlines()
        if len(lines) <= num_lines:
            return content

        return "\n".join(lines[-num_lines:])

    def build_system_prompt(self) -> str:
        """
        Construct the system prompt from agent core files.

        Returns:
            Formatted system prompt string.
        """
        agent_def = self._read_file("AGENT.md")
        soul_def = self._read_file("SOUL.md")
        user_profile = self._read_file("USER.md")
        notebook_tail = self._get_notebook_tail()

        if not user_profile:
            user_profile = "No user profile yet. Learn about the user through conversation."

        if not notebook_tail:
            notebook_tail = "No notes yet."

        prompt = f"""You are the Moon AI Head Agent. Below are your core identity files that define who you are, how you behave, and what you know about the current user.

=== AGENT DEFINITION (Capabilities & Rules) ===
{agent_def}

=== SOUL DEFINITION (Personality & Ethics) ===
{soul_def}

=== USER PROFILE ===
{user_profile}

=== WORKING NOTEBOOK (Recent Notes) ===
{notebook_tail}

=== INSTRUCTIONS ===
- Respond naturally based on your SOUL personality
- Follow all rules defined in your AGENT definition
- Reference USER profile to personalize responses
- Check NOTEBOOK for any pending tasks or context
- Keep responses helpful, direct, and conversational
"""
        return prompt

    def _build_conversation_history(self, current_message: str) -> List[Dict[str, str]]:
        """
        Build conversation history for the LLM.

        Args:
            current_message: The latest user message.

        Returns:
            List of message dictionaries [{"role": "user", "content": ...}, ...]
        """
        # Fetch last 20 messages
        recent_messages = get_recent_messages(limit=20)

        history = []
        for msg in recent_messages:
            role = "user" if msg.sender == "user" else "assistant"
            history.append({"role": role, "content": msg.content})

        # Append current message
        history.append({"role": "user", "content": current_message})

        return history

    async def process_message(self, user_message: str) -> AsyncGenerator[str, None]:
        """
        Process a user message through the agent think loop.

        1. Save user message
        2. Build context (system prompt + history)
        3. Stream from LLM
        4. Save full response to DB

        Args:
            user_message: The user's input message.

        Yields:
            Tokens from the LLM response.
        """
        # 1. Save user message immediately
        try:
            save_message(MessageCreate(sender="user", content=user_message))
        except Exception as e:
            logger.error(f"Failed to save user message: {e}")

        # 2. Build context
        system_prompt = self.build_system_prompt()
        conversation_history = self._build_conversation_history(user_message)

        full_messages = [{"role": "system", "content": system_prompt}] + conversation_history

        accumulated_response = ""

        # 3. Call LLM (or fallback)
        if not self.llm_service:
            fallback_msg = f"I'm not fully configured yet. Please set up your LLM_API_KEY in the .env file to enable AI responses. For now, I received your message: '{user_message[:100]}...'"
            accumulated_response = fallback_msg
            yield fallback_msg
        else:
            try:
                logger.info(f"Streaming message from LLM (History: {len(conversation_history)} msgs)")
                async for token in await self.llm_service.send_message(messages=full_messages, stream=True):
                    if token:
                        accumulated_response += token
                        yield token
            except Exception as e:
                logger.error(f"Error calling LLM: {e}")
                logger.debug(traceback.format_exc())
                error_msg = "\n\n[I encountered an issue processing your message. Please try again.]"
                accumulated_response += error_msg
                yield error_msg

        # 4. Save assistant response to DB
        if accumulated_response:
            try:
                save_message(MessageCreate(sender="assistant", content=accumulated_response))
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")


# Create global instance (lazy — will use global llm_service)
try:
    head_agent = HeadAgent()
except Exception as e:
    logger.warning(f"Head Agent not initialized: {e}")
    head_agent = None
