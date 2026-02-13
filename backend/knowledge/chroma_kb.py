"""ChromaDB-backed knowledge base for MindCast RAG.

Collections:
- history_archive    ── 往期节目对话、摘要、话题
- expert_opinions    ── 行业专家观点与言论
- fact_check         ── AI 新闻事实核查条目
- background_material── 重要话题的背景资料
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.knowledge.base import KnowledgeBase

logger = logging.getLogger(__name__)

# Collection names
HISTORY_ARCHIVE = "history_archive"
EXPERT_OPINIONS = "expert_opinions"
FACT_CHECK = "fact_check"
BACKGROUND_MATERIAL = "background_material"

ALL_COLLECTIONS = [HISTORY_ARCHIVE, EXPERT_OPINIONS,
                   FACT_CHECK, BACKGROUND_MATERIAL]


def _doc_id(text: str) -> str:
    """Deterministic short ID from text content."""
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class ChromaKnowledgeBase(KnowledgeBase):
    """Production knowledge base backed by ChromaDB (persistent storage).

    Parameters
    ----------
    persist_dir:
        Directory for the ChromaDB on-disk store.
    """

    def __init__(self, persist_dir: str | Path = "data/chromadb") -> None:
        persist_path = Path(persist_dir)
        persist_path.mkdir(parents=True, exist_ok=True)

        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Pre-create all collections
        self._collections: dict[str, chromadb.Collection] = {}
        for name in ALL_COLLECTIONS:
            self._collections[name] = self._client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )
        logger.info(
            "ChromaDB knowledge base initialized at %s with collections: %s",
            persist_path,
            ALL_COLLECTIONS,
        )

    # ------------------------------------------------------------------
    # Abstract interface implementation
    # ------------------------------------------------------------------

    async def store(
        self,
        doc: dict[str, Any],
        *,
        collection: str = BACKGROUND_MATERIAL,
    ) -> None:
        """Store a single document in the specified collection.

        *doc* must contain at least a ``"content"`` key.  Optional keys
        ``"metadata"`` and ``"id"`` are forwarded to ChromaDB.
        """
        coll = self._collections.get(collection)
        if coll is None:
            raise ValueError(f"Unknown collection: {collection}")

        content = doc.get("content", "")
        if not content:
            return

        doc_id = doc.get("id") or _doc_id(content)
        metadata = doc.get("metadata", {})
        metadata.setdefault("stored_at", datetime.now().isoformat())

        coll.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        logger.debug(
            "Stored doc %s in [%s] (len=%d)", doc_id, collection, len(content),
        )

    async def query(
        self,
        text: str,
        *,
        top_k: int = 5,
        collection: str = BACKGROUND_MATERIAL,
    ) -> list[dict[str, Any]]:
        """Retrieve the most relevant documents for *text*."""
        coll = self._collections.get(collection)
        if coll is None:
            return []

        # Guard against empty collection
        if coll.count() == 0:
            return []

        results = coll.query(
            query_texts=[text],
            n_results=min(top_k, coll.count()),
        )

        docs: list[dict[str, Any]] = []
        if results and results["documents"]:
            for i, doc_text in enumerate(results["documents"][0]):
                entry: dict[str, Any] = {"content": doc_text}
                if results["metadatas"] and results["metadatas"][0]:
                    entry["metadata"] = results["metadatas"][0][i]
                if results["distances"] and results["distances"][0]:
                    entry["distance"] = results["distances"][0][i]
                if results["ids"] and results["ids"][0]:
                    entry["id"] = results["ids"][0][i]
                docs.append(entry)
        return docs

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------

    async def store_many(
        self,
        docs: list[dict[str, Any]],
        *,
        collection: str = BACKGROUND_MATERIAL,
    ) -> int:
        """Batch-upsert multiple documents.  Returns the count stored."""
        coll = self._collections.get(collection)
        if coll is None:
            raise ValueError(f"Unknown collection: {collection}")

        ids: list[str] = []
        texts: list[str] = []
        metas: list[dict[str, Any]] = []

        for doc in docs:
            content = doc.get("content", "")
            if not content:
                continue
            doc_id = doc.get("id") or _doc_id(content)
            metadata = doc.get("metadata", {})
            metadata.setdefault("stored_at", datetime.now().isoformat())
            ids.append(doc_id)
            texts.append(content)
            metas.append(metadata)

        if not ids:
            return 0

        coll.upsert(ids=ids, documents=texts, metadatas=metas)
        logger.info("Batch-stored %d docs in [%s]", len(ids), collection)
        return len(ids)

    async def query_multiple_collections(
        self,
        text: str,
        *,
        collections: list[str] | None = None,
        top_k: int = 3,
    ) -> dict[str, list[dict[str, Any]]]:
        """Query across multiple collections and return results per collection."""
        target = collections or ALL_COLLECTIONS
        results: dict[str, list[dict[str, Any]]] = {}
        for coll_name in target:
            results[coll_name] = await self.query(
                text, top_k=top_k, collection=coll_name,
            )
        return results

    # ------------------------------------------------------------------
    # Domain-specific ingest methods
    # ------------------------------------------------------------------

    async def ingest_episode(
        self,
        episode_id: str,
        topic: str,
        summary: str,
        dialogue_lines: list[dict[str, str]],
        news_sources: list[dict[str, Any]] | None = None,
    ) -> None:
        """Ingest a completed episode into the history archive.

        Stores the full dialogue text and individual notable lines.
        """
        # Store episode summary
        await self.store(
            {
                "id": f"ep_{episode_id}_summary",
                "content": f"【话题】{topic}\n【摘要】{summary}",
                "metadata": {
                    "episode_id": episode_id,
                    "type": "episode_summary",
                    "topic": topic,
                },
            },
            collection=HISTORY_ARCHIVE,
        )

        # Store key dialogue lines (skip very short lines)
        notable_lines = [
            line for line in dialogue_lines
            if len(line.get("text", "")) > 30
        ]
        docs = []
        for i, line in enumerate(notable_lines):
            docs.append({
                "id": f"ep_{episode_id}_line_{i}",
                "content": f"[{line.get('speaker', '')}]: {line.get('text', '')}",
                "metadata": {
                    "episode_id": episode_id,
                    "speaker": line.get("speaker", ""),
                    "type": "dialogue_line",
                    "topic": topic,
                },
            })
        if docs:
            await self.store_many(docs, collection=HISTORY_ARCHIVE)

        # Store news sources as background material
        if news_sources:
            bg_docs = []
            for ns in news_sources:
                content = ns.get("content", "")
                if len(content) > 50:
                    bg_docs.append({
                        "content": f"【{ns.get('title', '')}】\n{content}",
                        "metadata": {
                            "type": "news_source",
                            "url": ns.get("url", ""),
                            "title": ns.get("title", ""),
                            "episode_id": episode_id,
                        },
                    })
            if bg_docs:
                await self.store_many(bg_docs, collection=BACKGROUND_MATERIAL)

        logger.info(
            "Ingested episode %s: summary + %d lines + %d news sources",
            episode_id,
            len(docs),
            len(news_sources or []),
        )

    async def ingest_expert_opinion(
        self,
        expert_name: str,
        opinion: str,
        source: str = "",
        topic: str = "",
    ) -> None:
        """Store an expert's opinion/quote for future reference."""
        await self.store(
            {
                "content": f"[{expert_name}]: {opinion}",
                "metadata": {
                    "expert": expert_name,
                    "source": source,
                    "topic": topic,
                    "type": "expert_opinion",
                },
            },
            collection=EXPERT_OPINIONS,
        )

    async def ingest_fact_check(
        self,
        claim: str,
        verdict: str,
        evidence: str = "",
        source: str = "",
    ) -> None:
        """Store a fact-check entry."""
        content = f"【声称】{claim}\n【核查结果】{verdict}"
        if evidence:
            content += f"\n【依据】{evidence}"
        await self.store(
            {
                "content": content,
                "metadata": {
                    "type": "fact_check",
                    "verdict": verdict,
                    "source": source,
                },
            },
            collection=FACT_CHECK,
        )

    async def ingest_background(
        self,
        topic: str,
        content: str,
        source: str = "",
    ) -> None:
        """Store background research material."""
        await self.store(
            {
                "content": content,
                "metadata": {
                    "topic": topic,
                    "source": source,
                    "type": "background",
                },
            },
            collection=BACKGROUND_MATERIAL,
        )

    # ------------------------------------------------------------------
    # RAG context builder
    # ------------------------------------------------------------------

    async def build_rag_context(
        self,
        topic: str,
        *,
        top_k_per_collection: int = 3,
    ) -> str:
        """Build a comprehensive RAG context block for a topic.

        Queries all four collections and formats the results into a single
        context string suitable for injection into agent prompts.
        """
        all_results = await self.query_multiple_collections(
            topic, top_k=top_k_per_collection,
        )

        sections: list[str] = []

        # History archive
        history_docs = all_results.get(HISTORY_ARCHIVE, [])
        if history_docs:
            lines = ["【往期相关讨论】"]
            for doc in history_docs:
                lines.append(f"  · {doc['content'][:200]}")
            sections.append("\n".join(lines))

        # Expert opinions
        expert_docs = all_results.get(EXPERT_OPINIONS, [])
        if expert_docs:
            lines = ["【专家观点参考】"]
            for doc in expert_docs:
                lines.append(f"  · {doc['content'][:200]}")
            sections.append("\n".join(lines))

        # Fact checks
        fact_docs = all_results.get(FACT_CHECK, [])
        if fact_docs:
            lines = ["【事实核查提醒】"]
            for doc in fact_docs:
                lines.append(f"  · {doc['content'][:200]}")
            sections.append("\n".join(lines))

        # Background material
        bg_docs = all_results.get(BACKGROUND_MATERIAL, [])
        if bg_docs:
            lines = ["【背景资料补充】"]
            for doc in bg_docs:
                lines.append(f"  · {doc['content'][:300]}")
            sections.append("\n".join(lines))

        if not sections:
            return ""

        return "\n\n".join(sections)

    def get_collection_stats(self) -> dict[str, int]:
        """Return document count per collection (for monitoring)."""
        return {name: coll.count() for name, coll in self._collections.items()}
