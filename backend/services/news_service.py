"""Tavily-based news fetching service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from math import ceil

from tavily import AsyncTavilyClient

from backend.config import settings
from backend.models import DetailedInfo, NewsItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt for LLM-based query expansion
# ---------------------------------------------------------------------------
_EXPAND_QUERIES_SYSTEM = """\
你是一位专业的新闻检索助手。用户给出了一个感兴趣的话题，请你为该话题生成3条各有侧重的中文搜索语句，\
用于从新闻数据库中检索最新、最相关的资讯。

要求：
1. 3条语句各有不同角度（如：最新动态、政策/影响、背景分析），避免重复
2. 每条语句简洁，50字以内
3. 必须包含话题的核心关键词
4. 只返回 JSON 数组，格式：["语句1","语句2","语句3"]，不要任何其他文字
"""


class NewsService:
    """Fetch topic-based news and perform deep searches via Tavily."""

    def __init__(self, api_key: str | None = None, llm=None) -> None:
        self._client = AsyncTavilyClient(
            api_key=api_key or settings.tavily_api_key)
        self._llm = llm  # optional LLMService; injected lazily if None

    @staticmethod
    def _doc_id(*parts: str) -> str:
        raw = "|".join(parts)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def _normalize_text(text: str) -> str:
        return re.sub(r"\s+", "", (text or "")).lower()

    @staticmethod
    def _extract_topic_terms(topic: str) -> list[str]:
        cleaned = (topic or "").strip()
        if not cleaned:
            return []

        parts = [p.strip()
                 for p in re.split(r"[\s,，。；;、|/]+", cleaned) if p.strip()]
        terms: list[str] = []
        seen: set[str] = set()

        for term in [cleaned, *parts]:
            normalized = NewsService._normalize_text(term)
            if len(normalized) < 2:
                continue
            if normalized in seen:
                continue
            seen.add(normalized)
            terms.append(term)

        return terms

    @staticmethod
    def _topic_match_count(item: NewsItem, topic_terms: list[str]) -> int:
        haystack = NewsService._normalize_text(f"{item.title} {item.content}")
        if not haystack or not topic_terms:
            return 0

        return sum(
            1
            for term in topic_terms
            if NewsService._normalize_text(term) in haystack
        )

    @staticmethod
    def _is_relevant_item(item: NewsItem, topic: str, topic_terms: list[str]) -> bool:
        haystack = NewsService._normalize_text(f"{item.title} {item.content}")
        normalized_topic = NewsService._normalize_text(topic)
        if not haystack or not normalized_topic:
            return False

        if normalized_topic in haystack:
            return True

        matched_terms = NewsService._topic_match_count(item, topic_terms)
        if len(topic_terms) <= 1:
            return matched_terms >= 1
        return matched_terms >= ceil(len(topic_terms) / 2)

    def _get_llm(self):
        if self._llm is None:
            from backend.services.llm_service import get_llm_service
            self._llm = get_llm_service()
        return self._llm

    async def _expand_queries_via_llm(self, topic: str) -> list[str]:
        """Use LLM to generate 3 varied search queries for the given topic."""
        try:
            llm = self._get_llm()
            messages = [
                {"role": "system", "content": _EXPAND_QUERIES_SYSTEM},
                {"role": "user", "content": f"话题：{topic}"},
            ]
            raw = await llm.chat(messages, temperature=0.5, max_tokens=256)
            raw = raw.strip()
            # Strip markdown fences if present
            raw = re.sub(r"^```[a-z]*\n?", "", raw,
                         flags=re.IGNORECASE).rstrip("`").strip()
            queries: list[str] = json.loads(raw)
            if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
                valid = [q.strip() for q in queries if q.strip()]
                if valid:
                    logger.info(
                        "LLM expanded queries for '%s': %s", topic, valid)
                    return valid[:4]
        except Exception as exc:
            logger.warning("LLM query expansion failed: %s", exc)
        # Fallback: hand-crafted queries
        return [
            f"{topic} 最新消息",
            f"{topic} 最新进展",
            f"{topic} 相关动态",
        ]

    async def _fetch_one_query(self, query: str, per_query_max: int) -> list[NewsItem]:
        """Run a single Tavily search and return NewsItem list."""
        try:
            response = await self._client.search(
                query=query,
                topic="news",
                time_range="week",
                max_results=per_query_max,
                include_answer=False,
            )
            return [
                NewsItem(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    published_date=r.get("published_date"),
                    score=r.get("score"),
                )
                for r in response.get("results", [])
                if r.get("title") or r.get("content")
            ]
        except Exception as exc:
            logger.warning(
                "Tavily search failed for query '%s': %s", query, exc)
            return []

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

    async def get_topic_news(
        self,
        topic: str = "",
        max_results: int = 6,
    ) -> list[NewsItem]:
        """Retrieve latest news for a given topic.

        When *topic* is provided:
          1. Use LLM to expand the topic into 3 varied search queries.
          2. Run all queries against Tavily in parallel.
          3. Deduplicate by URL, filter for topic relevance, and return
             the top *max_results* items sorted by relevance + Tavily score.

        If *topic* is empty, fall back to a single general trending query.
        """
        normalized_topic = topic.strip()

        if not normalized_topic:
            # Simple path: single general query
            logger.info(
                "Fetching general trending news (max %d)…", max_results)
            response = await self._client.search(
                query="今日热点 最新资讯",
                topic="news",
                time_range="week",
                max_results=max_results,
                include_answer=False,
            )
            items = [
                NewsItem(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    content=r.get("content", ""),
                    published_date=r.get("published_date"),
                    score=r.get("score"),
                )
                for r in response.get("results", [])
            ]
            await self._persist_daily_news(items)
            logger.info("Fetched %d general news items", len(items))
            return items[:max_results]

        # ── LLM → expanded queries ────────────────────────────────────────
        queries = await self._expand_queries_via_llm(normalized_topic)
        # Each sub-query fetches a bit more than needed; we'll pool and trim
        per_query_max = max(3, ceil((max_results * 2) / len(queries)))

        logger.info(
            "Fetching topic news: topic=%s, queries=%s, per_query_max=%d",
            normalized_topic, queries, per_query_max,
        )

        # ── Parallel Tavily calls ─────────────────────────────────────────
        all_results: list[list[NewsItem]] = await asyncio.gather(
            *[self._fetch_one_query(q, per_query_max) for q in queries]
        )

        # ── Deduplicate by URL (keep first occurrence) ────────────────────
        seen_urls: set[str] = set()
        pool: list[NewsItem] = []
        for batch in all_results:
            for item in batch:
                key = item.url.strip() if item.url.strip() else item.title.strip()
                if key and key not in seen_urls:
                    seen_urls.add(key)
                    pool.append(item)

        logger.info(
            "Pooled %d unique items from %d queries for topic '%s'",
            len(pool), len(queries), normalized_topic,
        )

        # ── Relevance filter + sort ───────────────────────────────────────
        topic_terms = self._extract_topic_terms(normalized_topic)
        relevant = [
            item for item in pool
            if self._is_relevant_item(item, normalized_topic, topic_terms)
        ]

        relevant.sort(
            key=lambda item: (
                self._topic_match_count(item, topic_terms),
                item.score if item.score is not None else 0.0,
            ),
            reverse=True,
        )

        # If strict filter left too few, fill remaining slots from the
        # unfiltered pool sorted by Tavily score (avoid returning 0)
        if len(relevant) < max_results:
            irrelevant = [i for i in pool if i not in relevant]
            irrelevant.sort(
                key=lambda item: item.score if item.score is not None else 0.0,
                reverse=True,
            )
            fill_count = max_results - len(relevant)
            relevant.extend(irrelevant[:fill_count])
            logger.warning(
                "Topic filter kept %d/%d; padded with %d fallback items",
                len(relevant) - fill_count, len(pool), fill_count,
            )

        result = relevant[:max_results]
        logger.info(
            "Returning %d news items for topic '%s'", len(
                result), normalized_topic
        )
        await self._persist_daily_news(result)
        return result

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
