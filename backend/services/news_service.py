"""Tavily-based news fetching service."""

from __future__ import annotations

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
