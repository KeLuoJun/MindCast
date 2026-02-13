"""Knowledge base package — ChromaDB-backed RAG for MindCast."""

from backend.knowledge.base import KnowledgeBase
from backend.knowledge.chroma_kb import ChromaKnowledgeBase

__all__ = ["KnowledgeBase", "ChromaKnowledgeBase", "get_knowledge_base"]

_kb_instance: ChromaKnowledgeBase | None = None


def get_knowledge_base() -> ChromaKnowledgeBase:
    """Return the singleton ChromaDB knowledge base instance."""
    global _kb_instance
    if _kb_instance is None:
        from backend.config import settings
        _kb_instance = ChromaKnowledgeBase(
            persist_dir=settings.chromadb_persist_dir)
    return _kb_instance
