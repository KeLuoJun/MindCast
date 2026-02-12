"""Test Tavily news service integration."""

import asyncio
import sys

from backend.services.news_service import NewsService


async def test_get_daily_news():
    """Verify we can fetch daily AI news from Tavily."""
    service = NewsService()
    items = await service.get_daily_ai_news(max_results=5)

    print(f"\n=== Fetched {len(items)} news items ===")
    for i, item in enumerate(items, 1):
        print(f"\n{i}. {item.title}")
        print(f"   URL: {item.url}")
        print(f"   Score: {item.score}")
        print(f"   Content: {item.content[:150]}…")

    assert len(items) > 0, "Should fetch at least one news item"
    assert items[0].title, "News item should have a title"
    print("\n✅ test_get_daily_news PASSED")


async def test_search_detail():
    """Verify deep search returns detailed information."""
    service = NewsService()
    info = await service.search_detail("GPT-5 发布时间 技术突破")

    print(f"\n=== Deep search: {info.query} ===")
    print(f"Answer: {info.answer[:200] if info.answer else 'N/A'}…")
    print(f"Results: {len(info.results)} items")

    assert len(info.results) > 0, "Should return search results"
    print("\n✅ test_search_detail PASSED")


if __name__ == "__main__":
    asyncio.run(test_get_daily_news())
    asyncio.run(test_search_detail())
