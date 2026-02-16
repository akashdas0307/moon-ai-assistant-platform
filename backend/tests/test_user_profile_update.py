import pytest
from unittest.mock import AsyncMock, patch
from backend.core.agent.head_agent import HeadAgent
from backend.models.message import Message
from datetime import datetime

# Fixtures for HeadAgent and mocks

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.send_message = AsyncMock(return_value="## Name\nTest User\n\n## Interests\nCoding")
    return service

@pytest.fixture
def head_agent(mock_llm_service, tmp_path):
    agent = HeadAgent(llm_service=mock_llm_service)
    agent.agent_files_dir = tmp_path
    # Create empty USER.md
    (tmp_path / "USER.md").write_text("", encoding="utf-8")
    return agent

@pytest.mark.asyncio
async def test_parse_profile_sections(head_agent):
    content = """## Name
John Doe

## Interests
Coding
AI
"""
    sections = head_agent._parse_profile_sections(content)
    assert sections["Name"] == "John Doe"
    assert sections["Interests"] == "Coding\nAI"

@pytest.mark.asyncio
async def test_merge_profile_sections(head_agent):
    # Case 1: Existing empty, new content
    merged = head_agent._merge_profile_sections("", "New Content", "Section")
    assert merged == "New Content"

    # Case 2: Existing content, new empty
    merged = head_agent._merge_profile_sections("Existing Content", "", "Section")
    assert merged == "Existing Content"

    # Case 3: Both have content
    merged = head_agent._merge_profile_sections("Existing", "New", "Section")
    assert "Existing" in merged
    assert "New" in merged
    assert "Additionally" in merged

    # Case 4: Duplicate content
    merged = head_agent._merge_profile_sections("Content", "Content", "Section")
    assert merged == "Content"

@pytest.mark.asyncio
async def test_profile_update_triggers_after_5_messages(head_agent):
    # Mock _update_user_profile to verify it's called
    head_agent._update_user_profile = AsyncMock()

    # Process 4 messages
    for i in range(4):
        head_agent._message_count_since_last_update = i
        # We need to mock save_message and get_recent_messages to avoid DB calls
        with patch("backend.core.agent.head_agent.save_message"),              patch("backend.core.agent.head_agent.get_recent_messages", return_value=[]):
            async for token in head_agent.process_message("test"):
                pass

    assert head_agent._update_user_profile.call_count == 0

    # Process 5th message
    head_agent._message_count_since_last_update = 4
    with patch("backend.core.agent.head_agent.save_message"),          patch("backend.core.agent.head_agent.get_recent_messages", return_value=[]):
        async for token in head_agent.process_message("test"):
            pass

    assert head_agent._update_user_profile.call_count == 1
    assert head_agent._message_count_since_last_update == 0

@pytest.mark.asyncio
async def test_update_user_profile_end_to_end(head_agent):
    # Mock recent messages
    mock_messages = [
        Message(id=1, sender="user", content="My name is Alice", timestamp=datetime.now()),
        Message(id=2, sender="assistant", content="Hello Alice", timestamp=datetime.now())
    ]

    with patch("backend.core.agent.head_agent.get_recent_messages", return_value=mock_messages):
        # Mock LLM response
        head_agent.llm_service.send_message.return_value = """## Name
Alice

## Interests
Testing
"""
        await head_agent._update_user_profile()

        # Verify USER.md content
        content = (head_agent.agent_files_dir / "USER.md").read_text(encoding="utf-8")
        assert "## Name" in content
        assert "Alice" in content
        assert "## Interests" in content
        assert "Testing" in content

        # Verify LLM call used cheap model
        call_args = head_agent.llm_service.send_message.call_args
        assert call_args.kwargs.get("model") == "gpt-3.5-turbo"

@pytest.mark.asyncio
async def test_update_handles_llm_failure(head_agent):
    head_agent.llm_service.send_message.side_effect = Exception("LLM Error")

    with patch("backend.core.agent.head_agent.get_recent_messages", return_value=[]):
        # Should not raise exception
        await head_agent._update_user_profile()
