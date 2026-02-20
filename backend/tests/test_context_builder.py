import pytest
from unittest.mock import AsyncMock, patch
from backend.core.agent.head_agent import HeadAgent
from backend.core.memory import CondensationEngine
from backend.models.message import Message
from datetime import datetime

# Helper for async generator
async def async_generator(items):
    for item in items:
        yield item

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.send_message.return_value = async_generator(["Mock ", "Response"])
    return service

@pytest.fixture
def mock_db_funcs():
    with patch("backend.core.agent.head_agent.get_recent_messages") as mock_get, \
         patch("backend.core.agent.head_agent.save_message") as mock_save:
        mock_get.return_value = []
        yield mock_get, mock_save

@pytest.fixture
def head_agent(mock_llm_service, tmp_path):
    # Setup minimal agent files
    agent_dir = tmp_path / "agents" / "head-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text("")
    (agent_dir / "SOUL.md").write_text("")
    (agent_dir / "USER.md").write_text("")
    (agent_dir / "NOTEBOOK.md").write_text("")

    agent = HeadAgent(llm_service=mock_llm_service)
    agent.agent_files_dir = agent_dir
    return agent

def test_condensation_engine_initialized_with_llm(head_agent):
    """Test that CondensationEngine is initialized when LLM service is present."""
    assert head_agent.condensation_engine is not None
    assert isinstance(head_agent.condensation_engine, CondensationEngine)
    assert head_agent.condensation_engine.llm_service == head_agent.llm_service

def test_condensation_engine_none_without_llm(tmp_path):
    """Test that CondensationEngine is None when LLM service is missing."""
    # Setup minimal agent files
    agent_dir = tmp_path / "agents" / "head-agent"
    agent_dir.mkdir(parents=True)
    (agent_dir / "AGENT.md").write_text("")

    # Patch global_llm_service to be None so fallback doesn't pick it up
    with patch("backend.core.agent.head_agent.global_llm_service", None):
        # Init with None llm_service
        agent = HeadAgent(llm_service=None)
        # Mock files dir to avoid errors if it tries to access
        agent.agent_files_dir = agent_dir

        assert agent.llm_service is None
        assert agent.condensation_engine is None

@pytest.mark.asyncio
async def test_process_message_calls_condense(head_agent, mock_db_funcs):
    """Test that process_message calls condense."""
    mock_get, _ = mock_db_funcs
    mock_get.return_value = [Message(id=1, sender="user", content="Hi", timestamp=datetime.now())]

    with patch.object(head_agent.condensation_engine, "condense", new_callable=AsyncMock) as mock_condense:
        mock_condense.side_effect = lambda msgs: msgs # Pass through

        async for _ in head_agent.process_message("Hello"):
            pass

        mock_condense.assert_called_once()
        # Verify it was called with a list of messages
        args, _ = mock_condense.call_args
        assert isinstance(args[0], list)
        assert len(args[0]) >= 2 # History + current

@pytest.mark.asyncio
async def test_process_message_uses_condensed_history(head_agent, mock_llm_service, mock_db_funcs):
    """Test that the condensed history is used for LLM call."""
    mock_get, _ = mock_db_funcs
    mock_get.return_value = [Message(id=1, sender="user", content="Hi", timestamp=datetime.now())]

    # Mock condense to return a modified list
    condensed_history = [{"role": "user", "content": "Condensed Context"}]

    with patch.object(head_agent.condensation_engine, "condense", new_callable=AsyncMock) as mock_condense:
        mock_condense.return_value = condensed_history

        async for _ in head_agent.process_message("Hello"):
            pass

        # Verify LLM call
        call_args = mock_llm_service.send_message.call_args
        messages = call_args.kwargs["messages"]

        # Structure: System + History (Condensed)
        assert len(messages) == 2 # System + 1 condensed msg
        assert messages[1] == condensed_history[0]

@pytest.mark.asyncio
async def test_process_message_survives_condensation_error(head_agent, mock_llm_service, mock_db_funcs):
    """Test that process_message falls back to raw history if condensation fails."""
    mock_get, _ = mock_db_funcs
    mock_get.return_value = [Message(id=1, sender="user", content="Hi", timestamp=datetime.now())]

    with patch.object(head_agent.condensation_engine, "condense", new_callable=AsyncMock) as mock_condense:
        mock_condense.side_effect = Exception("Condensation Explosion")

        async for _ in head_agent.process_message("Hello"):
            pass

        # Should still call LLM with raw history
        mock_llm_service.send_message.assert_called_once()
        call_args = mock_llm_service.send_message.call_args
        messages = call_args.kwargs["messages"]

        # Raw history should have: Hi, Hello
        # System + Hi + Hello = 3 messages
        assert len(messages) == 3
        assert messages[1]["content"] == "Hi"
        assert messages[2]["content"] == "Hello"

@pytest.mark.asyncio
async def test_no_condensation_when_engine_none(head_agent, mock_llm_service, mock_db_funcs):
    """Test behavior when condensation_engine is None manually set."""
    head_agent.condensation_engine = None
    mock_get, _ = mock_db_funcs
    mock_get.return_value = [Message(id=1, sender="user", content="Hi", timestamp=datetime.now())]

    # We can't mock condensation_engine.condense because it's None.
    # Just verify process_message runs and calls LLM with raw history.

    async for _ in head_agent.process_message("Hello"):
        pass

    mock_llm_service.send_message.assert_called_once()
    call_args = mock_llm_service.send_message.call_args
    messages = call_args.kwargs["messages"]

    assert len(messages) == 3 # System + Hi + Hello
