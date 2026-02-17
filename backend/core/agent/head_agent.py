"""Head Agent - Main agent think loop for Moon-AI system."""

import logging
from pathlib import Path
from typing import List, Dict, Optional, AsyncGenerator
import traceback
import re
from datetime import datetime

from backend.core.llm.service import LLMService, llm_service as global_llm_service
from backend.services.message_service import get_recent_messages, save_message
from backend.models.message import MessageCreate

logger = logging.getLogger(__name__)

# Path to agent core files
AGENT_FILES_DIR = Path(__file__).resolve().parent.parent.parent / "agents" / "head-agent"

PROFILE_ANALYSIS_PROMPT = """
You are analyzing conversation history to build a user profile. Extract key information about the user.

CONVERSATION HISTORY:
{conversation_history}

Based on these conversations, provide a structured profile with:

## Name
[User's name if mentioned, otherwise "Unknown"]

## Communication Style
[How they prefer to communicate: formal/casual, brief/detailed, etc.]

## Interests & Topics
[Topics they frequently discuss or show interest in]

## Preferences
[Any explicit preferences they've mentioned]

## Context
[Work, projects, location, or life context if relevant]

## Technical Level
[Beginner, Intermediate, Advanced - based on their questions and understanding]

## Patterns
[Any recurring patterns in their requests or communication]

IMPORTANT:
- Only include information that's clearly evident from the conversations
- Use "Unknown" or "Not specified" for unclear items
- Be concise — aim for 2-3 sentences per section
- Focus on actionable insights that help personalize future responses
"""

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

        # User profile update settings
        self.user_profile_update_interval = 5
        self._message_count_since_last_update = 0

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

    def _write_file(self, filename: str, content: str) -> None:
        """
        Write content to a file in the agent files directory.

        Args:
            filename: Name of the file to write (e.g., "USER.md")
            content: Content to write
        """
        file_path = self.agent_files_dir / filename
        try:
            file_path.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Error writing agent file {filename}: {e}")

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

    def _append_notebook_entry(self, content: str, tag: str = "[PENDING]") -> None:
        """
        Append a new entry to NOTEBOOK.md with timestamp and tag.

        Args:
            content: The note content
            tag: Entry tag ([PENDING], [COMPLETED], [INFO])
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"{tag} {timestamp} - {content}"

        current_content = self._read_file("NOTEBOOK.md")
        if current_content and not current_content.endswith("\n"):
            entry = f"\n{entry}"
        elif not current_content:
            entry = f"{entry}"
        else:
            entry = f"{entry}" # Already has newline at end of file usually, but append needs care

        # Append to file
        # We use read/write because _write_file overwrites.
        # We should append.
        full_content = current_content + ("\n" if current_content and not current_content.endswith("\n") else "") + entry
        self._write_file("NOTEBOOK.md", full_content)
        logger.info(f"Appended notebook entry: {entry}")

    def _find_entry_index(self, keyword: str) -> int:
        """
        Find the line index of a pending notebook entry matching the keyword.

        Args:
            keyword: Text to search for.

        Returns:
            Line index (0-based) or -1 if not found.
        """
        content = self._read_file("NOTEBOOK.md")
        if not content:
            return -1

        lines = content.splitlines()
        keyword_lower = keyword.lower()

        # Prefer exact match or significant overlap
        # Logic: find lines with [PENDING] that contain keyword
        for i, line in enumerate(lines):
            if "[PENDING]" in line and keyword_lower in line.lower():
                return i

        return -1

    def _mark_notebook_completed(self, entry_index: int) -> None:
        """
        Mark a specific notebook entry as [COMPLETED].

        Args:
            entry_index: Line number of the entry to mark (0-indexed)
        """
        content = self._read_file("NOTEBOOK.md")
        if not content:
            return

        lines = content.splitlines()
        if entry_index < 0 or entry_index >= len(lines):
            logger.warning(f"Invalid notebook entry index: {entry_index}")
            return

        line = lines[entry_index]
        if "[PENDING]" in line:
            lines[entry_index] = line.replace("[PENDING]", "[COMPLETED]")
            self._write_file("NOTEBOOK.md", "\n".join(lines))
            logger.info(f"Marked notebook entry {entry_index} as completed")

            # Auto-archive
            self._archive_completed_entries()

    def _archive_completed_entries(self) -> None:
        """
        Move all [COMPLETED] entries from NOTEBOOK.md to archived_notebook.md.
        Auto-called after marking items complete.
        """
        content = self._read_file("NOTEBOOK.md")
        if not content:
            return

        lines = content.splitlines()
        pending_lines = []
        completed_lines = []

        for line in lines:
            if "[COMPLETED]" in line:
                completed_lines.append(line)
            else:
                pending_lines.append(line)

        if not completed_lines:
            return

        # Write back NOTEBOOK.md
        self._write_file("NOTEBOOK.md", "\n".join(pending_lines))

        # Append to archived_notebook.md
        archive_content = self._read_file("archived_notebook.md")
        if not archive_content:
            archive_content = "# Archived Notebook Entries\n\n"

        new_archive_content = archive_content + ("\n" if archive_content and not archive_content.endswith("\n") else "") + "\n".join(completed_lines)
        self._write_file("archived_notebook.md", new_archive_content)
        logger.info(f"Archived {len(completed_lines)} entries")

    def _read_archived_notebook(self, num_lines: int = 15) -> str:
        """
        Read last N lines of archived_notebook.md for SPARK heartbeat checks.

        Args:
            num_lines: Number of lines to return from end

        Returns:
            String containing last N lines of archived notebook
        """
        content = self._read_file("archived_notebook.md")
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

=== NOTEBOOK USAGE INSTRUCTIONS ===
You can write notes to your NOTEBOOK.md for future reference using special syntax:
- To add a note: Include [NOTE: your note content here] anywhere in your response
- To mark a task complete: Include [COMPLETE: task description or keyword]
- Notes are automatically tagged with [PENDING] and timestamped
- Completed items are automatically archived to archived_notebook.md
- Keep notes brief and actionable for future reference
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

    def _parse_profile_sections(self, content: str) -> Dict[str, str]:
        """
        Parse markdown sections from USER.md.

        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        current_section = None
        current_content = []

        for line in content.split("\n"):
            if line.startswith("## "):
                # Save previous section
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                # Start new section
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _merge_profile_sections(self, existing: str, new: str, section_name: str) -> str:
        """
        Merge two profile sections intelligently.

        Args:
            existing: Current content from USER.md
            new: New content from LLM analysis
            section_name: Name of the section being merged

        Returns:
            Merged content
        """
        existing = existing.strip()
        new = new.strip()

        # If existing is empty or "Unknown", use new
        if not existing or existing.lower() in ["unknown", "not specified", "none"]:
            return new

        # If new is empty or "Unknown", keep existing
        if not new or new.lower() in ["unknown", "not specified", "none"]:
            return existing

        # Don't duplicate if content is very similar (simple check)
        if new in existing:
            return existing

        # Both have content — combine them
        return f"{existing}\n\nAdditionally: {new}"

    async def _update_user_profile(self) -> None:
        """
        Analyze recent conversation and update USER.md.
        """
        if not self.llm_service:
            return

        logger.info("Updating user profile based on recent messages...")

        try:
            # 1. Fetch recent messages
            recent_messages = get_recent_messages(limit=20)
            if not recent_messages:
                return

            conversation_text = ""
            for msg in recent_messages:
                conversation_text += f"{msg.sender.upper()}: {msg.content}\n"

            # 2. Build analysis prompt
            prompt = PROFILE_ANALYSIS_PROMPT.format(conversation_history=conversation_text)
            messages = [{"role": "user", "content": prompt}]

            # 3. Send to LLM (using cheap model)
            # Using openrouter/free as the default cheap model
            analysis = await self.llm_service.send_message(
                messages=messages,
                stream=False,
                model="openrouter/free"
            )

            # 4. Parse & Merge
            current_profile = self._read_file("USER.md")
            current_sections = self._parse_profile_sections(current_profile)
            new_sections = self._parse_profile_sections(analysis)

            # Get all unique section keys
            all_keys = set(current_sections.keys()) | set(new_sections.keys())

            # Use specific order if possible
            ordered_keys = [
                "Name", "Communication Style", "Interests & Topics",
                "Preferences", "Context", "Technical Level", "Patterns"
            ]

            # Add any custom sections found
            for key in all_keys:
                if key not in ordered_keys:
                    ordered_keys.append(key)

            final_content = "# User Profile\n\n"

            for key in ordered_keys:
                if key in all_keys:
                    existing_val = current_sections.get(key, "")
                    new_val = new_sections.get(key, "")
                    merged_val = self._merge_profile_sections(existing_val, new_val, key)
                    final_content += f"## {key}\n{merged_val}\n\n"

            # 5. Write back to USER.md
            self._write_file("USER.md", final_content)
            logger.info("User profile updated successfully.")

        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            logger.debug(traceback.format_exc())


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

        # 4. Process notebook commands and save response
        if accumulated_response:
            # Handle [NOTE: ...]
            # Use non-greedy match .*? to capture individual notes
            note_matches = re.findall(r"\[NOTE:(.*?)\]", accumulated_response, re.IGNORECASE)
            for note in note_matches:
                self._append_notebook_entry(note.strip())
                # Remove from response
                # Escape the note for regex replacement
                escaped_note = re.escape(note)
                # Use raw string for regex pattern
                accumulated_response = re.sub(rf"\[NOTE:{escaped_note}\]", "", accumulated_response, flags=re.IGNORECASE)

            # Handle [COMPLETE: ...]
            complete_matches = re.findall(r"\[COMPLETE:(.*?)\]", accumulated_response, re.IGNORECASE)
            for keyword in complete_matches:
                keyword = keyword.strip()
                idx = self._find_entry_index(keyword)
                if idx != -1:
                    self._mark_notebook_completed(idx)
                else:
                    logger.warning(f"Could not find notebook entry to complete: {keyword}")
                # Remove from response
                escaped_keyword = re.escape(keyword)
                accumulated_response = re.sub(rf"\[COMPLETE:{escaped_keyword}\]", "", accumulated_response, flags=re.IGNORECASE)

            try:
                save_message(MessageCreate(sender="assistant", content=accumulated_response))
            except Exception as e:
                logger.error(f"Failed to save assistant message: {e}")

        # 5. User Profile Update Logic
        self._message_count_since_last_update += 1
        if self._message_count_since_last_update >= self.user_profile_update_interval:
            # We don't want to block the response, but since this is an async generator,
            # we are already "done" yielding.
            # However, running this here means the generator won't finish until the update is done.
            # This is acceptable for a background process in this architecture.
            # In a more complex system, we might offload this to a task queue.
            await self._update_user_profile()
            self._message_count_since_last_update = 0


# Create global instance (lazy — will use global llm_service)
try:
    head_agent = HeadAgent()
except Exception as e:
    logger.warning(f"Head Agent not initialized: {e}")
    head_agent = None
