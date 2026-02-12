"""OpenAI-compatible LLM client with retry logic."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI

from backend.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Thin wrapper around an OpenAI-compatible async client."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.model = model or settings.llm_model
        self._client = AsyncOpenAI(
            base_url=base_url or settings.llm_base_url,
            api_key=api_key or settings.llm_api_key,
        )

    # ------------------------------------------------------------------
    # Core chat
    # ------------------------------------------------------------------

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.8,
        max_tokens: int = 4096,
        response_format: dict[str, Any] | None = None,
        retries: int = 3,
    ) -> str:
        """Send a chat completion request and return the assistant content."""
        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                kwargs: dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format

                resp = await self._client.chat.completions.create(**kwargs)
                content = resp.choices[0].message.content or ""
                return content.strip()
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "LLM request failed (attempt %d/%d): %s", attempt, retries, exc
                )
        raise RuntimeError(
            f"LLM request failed after {retries} retries") from last_error

    # ------------------------------------------------------------------
    # Streaming (reserved for future use)
    # ------------------------------------------------------------------

    async def chat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.8,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Yield streamed content chunks from the LLM."""
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content


# Module-level convenience instance (lazy)
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


llm_service: LLMService | None = None  # type: ignore[assignment]
