"""Base agent class wrapping LLM interactions."""

from __future__ import annotations

import logging

from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class BaseAgent:
    """Foundation for all podcast agents (host & guests).

    Each agent has a *system_prompt* that encodes its persona and
    maintains a running *conversation_history* for context continuity.
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        llm_service: LLMService,
    ) -> None:
        self.name = name
        self.system_prompt = system_prompt
        self.llm = llm_service
        self.conversation_history: list[dict[str, str]] = []

    # ------------------------------------------------------------------
    # Core thinking
    # ------------------------------------------------------------------

    async def think(
        self,
        user_message: str,
        *,
        conversation_history: list[dict[str, str]] | None = None,
        temperature: float = 0.85,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a response given the user message and optional shared history.

        If *conversation_history* is provided it is used instead of the
        agent's own history (useful for shared podcast conversation).
        """
        use_external_history = conversation_history is not None
        history = conversation_history if use_external_history else self.conversation_history

        messages = [
            {"role": "system", "content": self.system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        response = await self.llm.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Update internal history only when using internal memory mode.
        # In shared-context mode (conversation_history provided), writing to
        # self.conversation_history would duplicate state and grow unbounded.
        if not use_external_history:
            self.conversation_history.append(
                {"role": "user", "content": user_message})
            self.conversation_history.append(
                {"role": "assistant", "content": response})

        return response

    def reset_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history.clear()
