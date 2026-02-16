"""Tests for LLM service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.core.llm.service import LLMService


@pytest.fixture
def mock_settings():
    """Mock settings with LLM configuration."""
    with patch("backend.core.llm.service.settings") as mock:
        mock.llm_api_key = "sk-or-v1-test-key"
        mock.llm_model_name = "anthropic/claude-3.5-sonnet"
        mock.llm_base_url = "https://openrouter.ai/api/v1"
        yield mock


@pytest.fixture
def llm_service_instance(mock_settings):
    """Create LLM service instance with mocked settings."""
    return LLMService()


@pytest.mark.asyncio
async def test_service_initialization(llm_service_instance):
    """Test that service initializes correctly."""
    assert llm_service_instance.model == "anthropic/claude-3.5-sonnet"
    assert llm_service_instance.client is not None


@pytest.mark.asyncio
async def test_service_initialization_without_api_key():
    """Test that service raises error without API key."""
    with patch("backend.core.llm.service.settings") as mock_settings:
        mock_settings.llm_api_key = None
        mock_settings.llm_model_name = "test-model"

        with pytest.raises(ValueError, match="LLM_API_KEY"):
            LLMService()


@pytest.mark.asyncio
async def test_send_message_non_streaming(llm_service_instance):
    """Test non-streaming message sending."""
    # Mock the OpenAI client response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello! How can I help?"

    # Use AsyncMock for the create method
    with patch.object(
        llm_service_instance.client.chat.completions,
        "create",
        new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        response = await llm_service_instance.send_message(messages)

        assert response == "Hello! How can I help?"


@pytest.mark.asyncio
async def test_send_message_streaming(llm_service_instance):
    """Test streaming message sending."""
    # Mock streaming response
    class MockChunk:
        def __init__(self, content):
            self.choices = [MagicMock()]
            self.choices[0].delta.content = content

    async def mock_stream():
        for token in ["Hello", " ", "World", "!"]:
            yield MockChunk(token)

    # Use AsyncMock for the create method
    with patch.object(
        llm_service_instance.client.chat.completions,
        "create",
        new_callable=AsyncMock
    ) as mock_create:
        mock_create.return_value = mock_stream()

        messages = [{"role": "user", "content": "Hello"}]
        response_gen = await llm_service_instance.send_message(
            messages,
            stream=True
        )

        tokens = []
        async for token in response_gen:
            tokens.append(token)

        assert "".join(tokens) == "Hello World!"


@pytest.mark.asyncio
async def test_error_handling(llm_service_instance):
    """Test error handling for API failures."""
    with patch.object(
        llm_service_instance.client.chat.completions,
        "create",
        new_callable=AsyncMock
    ) as mock_create:
        mock_create.side_effect = Exception("API Error")

        messages = [{"role": "user", "content": "Hello"}]

        with pytest.raises(Exception, match="API Error"):
            await llm_service_instance.send_message(messages)
