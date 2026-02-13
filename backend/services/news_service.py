"""Tavily-based news fetching service."""

from __future__ import annotations

import hashlib
import logging

from tavily import AsyncTavilyClient

from backend.config import settings
from backend.models import DetailedInfo, NewsItem

logger = logging.getLogger(__name__)


class NewsService:
    """Fetch AI-related news and perform deep searches via Tavily."""

    def __init__(self, api_key: str | None = None) -> None:
        self._client = AsyncTavilyClient(
            api_key=api_key or settings.tavily_api_key)

    @staticmethod
    def _doc_id(*parts: str) -> str:
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    async def _persist_daily_news(self, items: list[NewsItem]) -> None:
        """Persist Tavily daily-news results into KB for long-term reuse."""
        if not items:
            return
        try:
            from backend.knowledge import get_knowledge_base
            from backend.knowledge.chroma_kb import (
                BACKGROUND_MATERIAL,
                KNOWLEDGE_SCOPE_GLOBAL,
            )

            kb = get_knowledge_base()
            docs: list[dict] = []
            for item in items:
                content = f"【新闻】{item.title}\n{item.content}"
                if len(content.strip()) < 20:
                    continue
                docs.append(
                    {
                        "id": self._doc_id("news", item.url or item.title, item.published_date or ""),
                        "content": content,
                        "metadata": {
                            "type": "tavily_daily_news",
                            "title": item.title,
                            "url": item.url,
                            "published_date": item.published_date,
                            "score": item.score,
                            "source": "tavily",
                            "topic": item.title,
                        },
                    }
                )

            if docs:
                await kb.store_many(
                    docs,
                    collection=BACKGROUND_MATERIAL,
                    scope=KNOWLEDGE_SCOPE_GLOBAL,
                )
        except Exception as exc:
            logger.warning("Persist daily news to KB failed: %s", exc)

    async def _persist_detail_search(
        self,
        query: str,
        answer: str | None,
        results: list[NewsItem],
    ) -> None:
        """Persist Tavily deep-search output into KB for future RAG retrieval."""
        try:
            from backend.knowledge import get_knowledge_base
            from backend.knowledge.chroma_kb import (
                BACKGROUND_MATERIAL,
                KNOWLEDGE_SCOPE_GLOBAL,
            )

            kb = get_knowledge_base()
            docs: list[dict] = []

            if answer and answer.strip():
                docs.append(
                    {
                        "id": self._doc_id("search_answer", query, answer[:200]),
                        "content": f"【检索问题】{query}\n【综合回答】{answer}",
                        "metadata": {
                            "type": "tavily_search_answer",
                            "query": query,
                            "source": "tavily",
                            "topic": query,
                        },
                    }
                )

            for item in results:
                content = f"【{item.title}】\n{item.content}"
                if len(content.strip()) < 20:
                    continue
                docs.append(
                    {
                        "id": self._doc_id("search_result", query, item.url or item.title),
                        "content": content,
                        "metadata": {
                            "type": "tavily_search_result",
                            "query": query,
                            "title": item.title,
                            "url": item.url,
                            "published_date": item.published_date,
                            "score": item.score,
                            "source": "tavily",
                            "topic": query,
                        },
                    }
                )

            if docs:
                await kb.store_many(
                    docs,
                    collection=BACKGROUND_MATERIAL,
                    scope=KNOWLEDGE_SCOPE_GLOBAL,
                )
        except Exception as exc:
            logger.warning("Persist detailed search to KB failed: %s", exc)

    async def get_daily_ai_news(self, max_results: int = 10) -> list[NewsItem]:
        """Retrieve today's AI news headlines and summaries."""
        logger.info("Fetching daily AI news (max %d results)…", max_results)
        response = await self._client.search(
            query="AI 人工智能 最新资讯",
            topic="news",
            time_range="week",
            max_results=max_results,
            include_answer=True,
        )
        items: list[NewsItem] = []
        for r in response.get("results", []):
            items.append(
                NewsItem(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    published_date=r.get("published_date"),
                    score=r.get("score"),
                )
            )
        await self._persist_daily_news(items)
        logger.info("Fetched %d news items", len(items))
        return items

    async def search_detail(
        self,
        query: str,
        *,
        search_depth: str = "advanced",
        max_results: int = 5,
    ) -> DetailedInfo:
        """Perform an in-depth search for a specific topic / angle."""
        logger.info("Deep search: %s", query)
        response = await self._client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=True,
        )
        results = [
            NewsItem(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                published_date=r.get("published_date"),
                score=r.get("score"),
            )
            for r in response.get("results", [])
        ]
        await self._persist_detail_search(
            query=query,
            answer=response.get("answer"),
            results=results,
        )
        return DetailedInfo(
            query=query,
            answer=response.get("answer"),
            results=results,
        )


# Module-level convenience instance (lazy to avoid missing-key errors on import)
_news_service: NewsService | None = None


def get_news_service() -> NewsService:
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


# Backward-compat alias
news_service: NewsService | None = None  # type: ignore[assignment]
