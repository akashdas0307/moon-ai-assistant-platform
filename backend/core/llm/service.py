from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM APIs via OpenRouter."""

    def __init__(self):
        """Initialize OpenRouter client with settings."""
        if not settings.llm_api_key:
            raise ValueError("LLM_API_KEY environment variable is required")

        if not settings.llm_model_name:
            raise ValueError("LLM_MODEL_NAME environment variable is required")

        # Default to OpenRouter if no base URL provided
        base_url = settings.llm_base_url or "https://openrouter.ai/api/v1"

        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/yourusername/moon-ai",  # Optional
                "X-Title": "Moon-AI-Assistant-Platform",
            }
        )
        self.model = settings.llm_model_name

        logger.info(f"LLM Service initialized with model: {self.model}")

    async def send_message(
        self,
        messages: list[dict],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str | AsyncGenerator[str, None]:
        """
        Send messages to LLM and get response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream response token-by-token
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Complete response string if stream=False,
            AsyncGenerator yielding tokens if stream=True
        """
        try:
            if stream:
                return self._stream_response(messages, temperature, max_tokens)
            else:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            raise

    async def _stream_response(
        self,
        messages: list[dict],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Helper for streaming token-by-token responses."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Error streaming LLM response: {e}")
            raise

# Global instance
try:
    llm_service = LLMService()
except ValueError as e:
    logger.warning(f"LLM Service not initialized: {e}")
    llm_service = None
