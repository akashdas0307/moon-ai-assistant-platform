import pytest
import os
from unittest.mock import AsyncMock
from backend.core.agent.head_agent import HeadAgent
from backend.models.message import MessageCreate
from backend.services.message_service import save_message, get_recent_messages
from backend.database.db import init_db

# Override DB for testing
import backend.database.db
original_db_path = backend.database.db.DB_PATH

@pytest.fixture
def test_db(tmp_path):
    # Set DB path to temp file
    db_file = tmp_path / "test_messages.db"
    backend.database.db.DB_PATH = db_file

    # Initialize DB
    init_db()

    yield

    # Teardown
    if db_file.exists():
        os.remove(db_file)
    backend.database.db.DB_PATH = original_db_path

@pytest.fixture
def mock_llm_service():
    service = AsyncMock()
    service.send_message = AsyncMock(return_value="## Name\nIntegration User\n\n## Interests\nIntegration Testing")
    return service

@pytest.fixture
def head_agent(mock_llm_service, tmp_path):
    agent = HeadAgent(llm_service=mock_llm_service)
    agent.agent_files_dir = tmp_path
    # Create empty USER.md
    (tmp_path / "USER.md").write_text("", encoding="utf-8")
    return agent

@pytest.mark.asyncio
async def test_integration_update_user_profile(head_agent, test_db):
    # Insert messages into DB using real service
    save_message(MessageCreate(sender="user", content="My name is Integration User"))
    save_message(MessageCreate(sender="assistant", content="Hello Integration User"))

    # Verify messages are in DB
    msgs = get_recent_messages(limit=10)
    assert len(msgs) == 2

    # Run update profile without mocking get_recent_messages
    # We still mock LLM service because we don't want to call OpenAI
    await head_agent._update_user_profile()

    # Verify USER.md content
    content = (head_agent.agent_files_dir / "USER.md").read_text(encoding="utf-8")
    assert "## Name" in content
    assert "Integration User" in content
