"""Test Agent system — persona prompts and dialogue generation."""

import asyncio

from backend.agents.host import HostAgent
from backend.agents.guest import GuestAgent
from backend.agents.personas import GUEST_PERSONAS, HOST_PERSONA
from backend.models import NewsItem
from backend.services.llm_service import LLMService


async def test_host_select_topic():
    """Verify the host agent can select a topic from news items."""
    llm = LLMService()
    host = HostAgent(llm)

    # Simulated news
    news = [
        NewsItem(title="OpenAI发布GPT-5", url="https://example.com/1",
                 content="OpenAI今日正式发布GPT-5大模型，在推理、编程等能力上取得显著突破。"),
        NewsItem(title="欧盟AI法案正式生效", url="https://example.com/2",
                 content="欧盟《人工智能法案》正式生效实施，对高风险AI系统提出严格监管要求。"),
        NewsItem(title="AI Agent自动编程效率超人类", url="https://example.com/3",
                 content="最新研究显示AI Agent在特定编程任务上效率已超过人类工程师。"),
    ]

    topic = await host.select_topic(news)
    print(f"\n=== Host Topic Selection ===")
    print(f"Selected: {topic}")
    assert "topic" in topic, "Should return a topic field"
    print("\n✅ test_host_select_topic PASSED")


async def test_guest_generate_line():
    """Verify a guest agent can generate a dialogue line."""
    llm = LLMService()
    guest = GuestAgent(GUEST_PERSONAS[0], llm)

    context = [
        {"role": "assistant",
         "content": "[林晨曦]: 欢迎各位！今天我们来聊聊GPT-5发布带来的影响。赵明远，你怎么看？"}
    ]

    line = await guest.generate_line(
        context,
        "回应主持人关于GPT-5的讨论，从AI算法工程师的视角发表看法。",
    )

    print(f"\n=== Guest Line Generation ===")
    print(f"Speaker: {line.speaker}")
    print(f"Text: {line.text}")
    print(f"SSML: {line.ssml_text}")
    print(f"Emotion: {line.emotion}")

    assert line.speaker == "赵明远"
    assert len(line.text) > 0
    print("\n✅ test_guest_generate_line PASSED")


if __name__ == "__main__":
    asyncio.run(test_host_select_topic())
    asyncio.run(test_guest_generate_line())
