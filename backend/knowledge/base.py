"""Knowledge base interface — placeholder for future RAG integration.

MVP implements a DummyKnowledgeBase that performs no operations.
Replace with ChromaDB-backed implementation when ready.
"""

from __future__ import annotations

import abc
from typing import Any


class KnowledgeBase(abc.ABC):
    """Abstract interface for a vector knowledge store."""

    @abc.abstractmethod
    async def store(self, doc: dict[str, Any], *, collection: str = "default") -> None:
        """Store a document in the knowledge base."""
        ...

    @abc.abstractmethod
    async def query(
        self, text: str, *, top_k: int = 5, collection: str = "default"
    ) -> list[dict[str, Any]]:
        """Retrieve the most relevant documents for *text*."""
        ...


class DummyKnowledgeBase(KnowledgeBase):
    """No-op implementation for the MVP stage."""

    async def store(self, doc: dict[str, Any], *, collection: str = "default") -> None:
        pass  # intentionally empty

    async def query(
        self, text: str, *, top_k: int = 5, collection: str = "default"
    ) -> list[dict[str, Any]]:
        return []


# Module-level instance
knowledge_base: KnowledgeBase = DummyKnowledgeBase()
