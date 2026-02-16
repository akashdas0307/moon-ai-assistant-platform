import pytest
import re
from unittest.mock import AsyncMock, patch
from backend.core.agent.head_agent import HeadAgent

# Mock definitions
MOCK_AGENT_MD = "Mock Agent"
MOCK_SOUL_MD = "Mock Soul"
MOCK_USER_MD = "Mock User"
MOCK_NOTEBOOK_MD = "Line 1\nLine 2\nLine 3"
MOCK_ARCHIVED_NOTEBOOK_MD = "# Archived Notebook Entries\n\n> Purpose: ...\n\n---\n\n(Archived entries will appear here automatically)"

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    # Ensure send_message is an AsyncMock
    service.send_message = AsyncMock()
    return service

@pytest.fixture
def head_agent(mock_llm_service, tmp_path):
    # Create temp agent files
    agent_dir = tmp_path / "agents" / "head-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text(MOCK_AGENT_MD)
    (agent_dir / "SOUL.md").write_text(MOCK_SOUL_MD)
    (agent_dir / "USER.md").write_text(MOCK_USER_MD)
    (agent_dir / "NOTEBOOK.md").write_text(MOCK_NOTEBOOK_MD)
    (agent_dir / "archived_notebook.md").write_text(MOCK_ARCHIVED_NOTEBOOK_MD)

    agent = HeadAgent(llm_service=mock_llm_service)
    agent.agent_files_dir = agent_dir
    return agent

def test_append_notebook_entry(head_agent):
    """Test adding a new notebook entry."""
    head_agent._append_notebook_entry("New Task", tag="[PENDING]")

    content = (head_agent.agent_files_dir / "NOTEBOOK.md").read_text()
    lines = content.splitlines()
    last_line = lines[-1]

    assert "[PENDING]" in last_line
    assert "New Task" in last_line
    # Check for timestamp format roughly
    assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", last_line)

def test_mark_notebook_completed(head_agent):
    """Test marking an entry as completed."""
    # Setup: add a pending task
    original_content = "Task 1\n[PENDING] 2023-01-01 10:00 - Task to complete\nTask 3"
    (head_agent.agent_files_dir / "NOTEBOOK.md").write_text(original_content)

    # We need to find the index of the line with [PENDING]
    # In this mock setup, it's line index 1 (0-based)
    head_agent._mark_notebook_completed(1)

    content = (head_agent.agent_files_dir / "NOTEBOOK.md").read_text()

    # Since completed items are auto-archived, it should be GONE from NOTEBOOK.md
    assert "[COMPLETED]" not in content
    assert "Task to complete" not in content

    # And present in archived_notebook.md
    archive_content = (head_agent.agent_files_dir / "archived_notebook.md").read_text()
    assert "[COMPLETED]" in archive_content
    assert "Task to complete" in archive_content

def test_archive_completed_entries_direct(head_agent):
    """Test archival logic directly."""
    # Setup NOTEBOOK with mixed entries
    notebook_content = """[PENDING] Task 1
[COMPLETED] 2023-01-01 10:00 - Done Task
[PENDING] Task 2
"""
    (head_agent.agent_files_dir / "NOTEBOOK.md").write_text(notebook_content)

    head_agent._archive_completed_entries()

    # Verify NOTEBOOK.md only has PENDING
    new_notebook = (head_agent.agent_files_dir / "NOTEBOOK.md").read_text()
    assert "[COMPLETED]" not in new_notebook
    assert "Done Task" not in new_notebook
    assert "Task 1" in new_notebook
    assert "Task 2" in new_notebook

    # Verify archived_notebook.md has COMPLETED
    archive = (head_agent.agent_files_dir / "archived_notebook.md").read_text()
    assert "Done Task" in archive

def test_read_archived_notebook(head_agent):
    """Test reading archived entries."""
    # Setup archive
    archive_content = "Header\n\n" + "\n".join([f"Line {i}" for i in range(20)])
    (head_agent.agent_files_dir / "archived_notebook.md").write_text(archive_content)

    tail = head_agent._read_archived_notebook(5)
    lines = tail.splitlines()
    assert len(lines) == 5
    assert lines[-1] == "Line 19"
    assert lines[0] == "Line 15"

@pytest.mark.asyncio
async def test_special_output_parsing_note(head_agent, mock_llm_service):
    """Test [NOTE:...] extraction from agent response."""
    # Mock LLM response with a note
    # We need to mock the async generator response of send_message
    async def mock_gen():
        yield "I will do this. "
        yield "[NOTE: Remember to buy milk]"

    # Set the return value of send_message to be the async generator object
    mock_llm_service.send_message.return_value = mock_gen()

    # We also need to mock save_message to capture what's saved
    with patch("backend.core.agent.head_agent.save_message") as mock_save, \
         patch("backend.core.agent.head_agent.get_recent_messages", return_value=[]):
        # Run process_message
        response_tokens = []
        async for token in head_agent.process_message("User input"):
            response_tokens.append(token)


        # Verify NOTEBOOK.md has the note
        notebook_content = (head_agent.agent_files_dir / "NOTEBOOK.md").read_text()
        assert "Remember to buy milk" in notebook_content

        # Verify saved message does NOT have the note (cleaned)
        # Check the call to save_message for assistant response
        # It's the second call (first is user message)
        assert mock_save.call_count == 2
        saved_msg = mock_save.call_args_list[1][0][0].content
        assert "Remember to buy milk" not in saved_msg
        assert "I will do this." in saved_msg

@pytest.mark.asyncio
async def test_special_output_parsing_complete(head_agent, mock_llm_service):
    """Test [COMPLETE:...] extraction and archival."""
    # Setup: Add a pending task to notebook
    head_agent._append_notebook_entry("Buy milk", tag="[PENDING]")

    # Mock LLM response
    async def mock_gen():
        yield "Done. "
        yield "[COMPLETE: Buy milk]"

    mock_llm_service.send_message.return_value = mock_gen()

    with patch("backend.core.agent.head_agent.save_message"), \
         patch("backend.core.agent.head_agent.get_recent_messages", return_value=[]):
        # Run process_message
        response_tokens = []
        async for token in head_agent.process_message("User input"):
            response_tokens.append(token)

        # Verify item moved to archive
        archive = (head_agent.agent_files_dir / "archived_notebook.md").read_text()
        assert "Buy milk" in archive

        # Verify item removed from notebook
        notebook = (head_agent.agent_files_dir / "NOTEBOOK.md").read_text()
        assert "Buy milk" not in notebook

def test_find_entry_index(head_agent):
    """Test finding entry index by keyword."""
    content = """Line 1
[PENDING] 2023-01-01 - Task A
[PENDING] 2023-01-01 - Task B
"""
    (head_agent.agent_files_dir / "NOTEBOOK.md").write_text(content)

    idx_a = head_agent._find_entry_index("Task A")
    assert idx_a == 1

    idx_b = head_agent._find_entry_index("Task B")
    assert idx_b == 2

    idx_missing = head_agent._find_entry_index("Task C")
    assert idx_missing == -1
