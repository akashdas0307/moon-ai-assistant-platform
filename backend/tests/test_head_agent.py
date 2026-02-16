import pytest
from unittest.mock import AsyncMock, patch
from backend.core.agent.head_agent import HeadAgent
from backend.models.message import Message
from datetime import datetime

# Mock data
MOCK_AGENT_MD = "Mock Agent Definition"
MOCK_SOUL_MD = "Mock Soul Definition"
MOCK_USER_MD = "Mock User Profile"
MOCK_NOTEBOOK_MD = "Line 1\nLine 2\nLine 3"

# Helper for async generator
async def async_generator(items):
    for item in items:
        yield item

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    # Default behavior: stream tokens
    service.send_message.return_value = async_generator(["Mock ", "AI ", "Response"])
    return service

@pytest.fixture
def mock_db_funcs():
    with patch("backend.core.agent.head_agent.get_recent_messages") as mock_get,          patch("backend.core.agent.head_agent.save_message") as mock_save:
        mock_get.return_value = []
        yield mock_get, mock_save

@pytest.fixture
def head_agent(mock_llm_service, tmp_path):
    # Create temp agent files
    agent_dir = tmp_path / "agents" / "head-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text(MOCK_AGENT_MD)
    (agent_dir / "SOUL.md").write_text(MOCK_SOUL_MD)
    (agent_dir / "USER.md").write_text(MOCK_USER_MD)
    (agent_dir / "NOTEBOOK.md").write_text(MOCK_NOTEBOOK_MD)

    agent = HeadAgent(llm_service=mock_llm_service)
    agent.agent_files_dir = agent_dir
    return agent

@pytest.mark.asyncio
async def test_head_agent_initialization(head_agent, mock_llm_service):
    """Test that HeadAgent initializes correctly."""
    assert head_agent.llm_service == mock_llm_service
    assert head_agent.agent_files_dir.exists()

def test_read_agent_files(head_agent):
    """Test reading agent files."""
    assert head_agent._read_file("AGENT.md") == MOCK_AGENT_MD
    assert head_agent._read_file("SOUL.md") == MOCK_SOUL_MD
    assert head_agent._read_file("USER.md") == MOCK_USER_MD

def test_read_missing_file(head_agent):
    """Test reading a missing file returns empty string."""
    assert head_agent._read_file("MISSING.md") == ""

def test_notebook_tail(head_agent, tmp_path):
    """Test getting the tail of the notebook."""
    # Test with small file
    assert head_agent._get_notebook_tail(15) == MOCK_NOTEBOOK_MD

    # Test with large file
    large_content = "\n".join([f"Line {i}" for i in range(20)])
    (head_agent.agent_files_dir / "NOTEBOOK.md").write_text(large_content)
    tail = head_agent._get_notebook_tail(15)
    assert len(tail.splitlines()) == 15
    assert tail.endswith("Line 19")
    assert tail.startswith("Line 5")

def test_build_system_prompt(head_agent):
    """Test building the system prompt."""
    prompt = head_agent.build_system_prompt()
    assert MOCK_AGENT_MD in prompt
    assert MOCK_SOUL_MD in prompt
    assert MOCK_USER_MD in prompt
    assert "Line 1" in prompt  # From notebook
    assert "=== AGENT DEFINITION" in prompt
    assert "=== SOUL DEFINITION" in prompt

def test_build_conversation_history(head_agent, mock_db_funcs):
    """Test building conversation history."""
    mock_get, _ = mock_db_funcs

    # Mock previous messages
    mock_get.return_value = [
        Message(id=1, sender="user", content="Hello", timestamp=datetime.now()),
        Message(id=2, sender="assistant", content="Hi there", timestamp=datetime.now())
    ]

    history = head_agent._build_conversation_history("How are you?")

    assert len(history) == 3
    assert history[0] == {"role": "user", "content": "Hello"}
    assert history[1] == {"role": "assistant", "content": "Hi there"}
    assert history[2] == {"role": "user", "content": "How are you?"}

@pytest.mark.asyncio
async def test_process_message(head_agent, mock_llm_service, mock_db_funcs):
    """Test processing a message through the full loop (streaming)."""
    mock_get, mock_save = mock_db_funcs

    # Collect tokens from generator
    tokens = []
    async for token in head_agent.process_message("Hello AI"):
        tokens.append(token)

    response = "".join(tokens)
    assert response == "Mock AI Response"

    # Verify LLM called with stream=True
    mock_llm_service.send_message.assert_called_once()
    call_args = mock_llm_service.send_message.call_args
    assert call_args.kwargs["stream"] is True
    messages = call_args.kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Hello AI"

    # Verify DB saves (user msg + assistant msg)
    assert mock_save.call_count == 2

    # Check first save (user) - happens before streaming
    assert mock_save.call_args_list[0][0][0].sender == "user"
    assert mock_save.call_args_list[0][0][0].content == "Hello AI"

    # Check second save (assistant) - happens after streaming
    assert mock_save.call_args_list[1][0][0].sender == "assistant"
    assert mock_save.call_args_list[1][0][0].content == "Mock AI Response"

@pytest.mark.asyncio
async def test_process_message_no_llm(head_agent, mock_db_funcs):
    """Test processing message without LLM service."""
    head_agent.llm_service = None
    _, mock_save = mock_db_funcs

    tokens = []
    async for token in head_agent.process_message("Hello"):
        tokens.append(token)

    response = "".join(tokens)

    assert "not fully configured" in response
    assert "Hello" in response

    # Verify DB saves
    assert mock_save.call_count == 2
    assert mock_save.call_args_list[1][0][0].sender == "assistant"
    assert mock_save.call_args_list[1][0][0].content == response

@pytest.mark.asyncio
async def test_process_message_llm_error(head_agent, mock_llm_service, mock_db_funcs):
    """Test handling LLM errors during streaming."""
    # Mock send_message to raise an exception immediately or during iteration
    # If send_message returns a coroutine that raises, or returns a generator that raises
    mock_llm_service.send_message.side_effect = Exception("LLM Error")
    _, mock_save = mock_db_funcs

    tokens = []
    async for token in head_agent.process_message("Hello"):
        tokens.append(token)

    response = "".join(tokens)

    assert "encountered an issue" in response

    # Verify DB saves (user msg + error msg)
    assert mock_save.call_count == 2
    assert mock_save.call_args_list[1][0][0].sender == "assistant"
    assert mock_save.call_args_list[1][0][0].content == response
