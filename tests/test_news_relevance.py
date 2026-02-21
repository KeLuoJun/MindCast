from backend.models import NewsItem
from backend.services.news_service import NewsService


class _FakeClient:
    async def search(self, **kwargs):
        return {
            "results": [
                {
                    "title": "US election update: Trump campaign shifts focus",
                    "url": "https://example.com/1",
                    "content": "Latest update on campaign strategy and policy debate.",
                    "published_date": "2026-02-22",
                    "score": 0.95,
                },
                {
                    "title": "Global market reacts to policy signals",
                    "url": "https://example.com/2",
                    "content": "Investors track trade and rate expectations.",
                    "published_date": "2026-02-22",
                    "score": 0.84,
                },
            ]
        }


def test_extract_topic_terms_keeps_core_phrase_and_parts():
    terms = NewsService._extract_topic_terms("特朗普 关税")

    assert "特朗普 关税" in terms
    assert "特朗普" in terms
    assert "关税" in terms


def test_is_relevant_item_rejects_unrelated_topic_news():
    topic = "特朗普"
    terms = NewsService._extract_topic_terms(topic)

    relevant = NewsItem(
        title="特朗普在竞选集会上谈及贸易政策",
        url="https://example.com/relevant",
        content="特朗普表示将调整关税方案。",
        published_date=None,
        score=0.93,
    )
    unrelated = NewsItem(
        title="冬奥会赛程更新：短道速滑今日开赛",
        url="https://example.com/unrelated",
        content="多国选手参赛，赛场氛围火热。",
        published_date=None,
        score=0.91,
    )

    assert NewsService._is_relevant_item(relevant, topic, terms) is True
    assert NewsService._is_relevant_item(unrelated, topic, terms) is False


def test_is_relevant_item_requires_multi_term_overlap_for_compound_topic():
    topic = "特朗普 关税"
    terms = NewsService._extract_topic_terms(topic)

    item = NewsItem(
        title="白宫发布最新外交声明",
        url="https://example.com/mid",
        content="声明提到特朗普，但未涉及贸易或关税。",
        published_date=None,
        score=0.89,
    )

    assert NewsService._is_relevant_item(item, topic, terms) is False


async def test_get_topic_news_fallback_to_raw_results_when_filter_empty():
    service = NewsService(api_key="test")
    service._client = _FakeClient()

    items = await service.get_topic_news(topic="特朗普", max_results=10)

    assert len(items) == 2
