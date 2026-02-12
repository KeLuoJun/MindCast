"""Host agent — topic selection, episode planning, and line generation."""

from __future__ import annotations

import json
import logging

from backend.agents.base import BaseAgent
from backend.agents.personas import HOST_PERSONA, build_system_prompt
from backend.models import DialogueLine, EpisodePlan, NewsItem
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class HostAgent(BaseAgent):
    """The podcast host: selects topics, plans episodes, drives conversation."""

    def __init__(self, llm_service: LLMService) -> None:
        super().__init__(
            name=HOST_PERSONA.name,
            system_prompt=build_system_prompt(HOST_PERSONA, is_host=True),
            llm_service=llm_service,
        )
        self.persona = HOST_PERSONA

    # ------------------------------------------------------------------
    # Topic selection
    # ------------------------------------------------------------------

    async def select_topic(self, news_list: list[NewsItem]) -> dict:
        """Pick the most compelling topic direction from a list of news items.

        Returns a dict with keys: ``index``, ``topic``, ``reason``, ``search_queries``.
        """
        news_summary = "\n".join(
            f"{i+1}. 【{item.title}】{item.content[:200]}"
            for i, item in enumerate(news_list)
        )

        prompt = f"""以下是今天获取到的{len(news_list)}条AI相关资讯：

{news_summary}

请你作为播客主持人，从中挑选**1个最具讨论价值的方向**来做今天这期播客。

选择标准：
1. 话题热度和时效性
2. 能引发多角度深度讨论（技术、商业、伦理等维度）
3. 对听众有实际价值和启发
4. 适合5分钟通勤播客的深度

请以JSON格式返回你的选择（不要包含markdown代码块标记）：
{{
    "index": 选中的新闻序号,
    "topic": "提炼的播客话题方向（一句话）",
    "reason": "选择理由（2-3句话）",
    "search_queries": ["后续深度搜索关键词1", "关键词2", "关键词3", "关键词4", "关键词5"]
}}"""

        response = await self.think(prompt, temperature=0.7, max_tokens=1024)

        try:
            # Strip possible markdown code fences
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error("Failed to parse topic selection JSON: %s", response)
            # Fallback: use the first news item
            return {
                "index": 1,
                "topic": news_list[0].title if news_list else "AI最新动态",
                "reason": "默认选择首条资讯",
                "search_queries": [news_list[0].title] if news_list else ["AI最新动态"],
            }

    # ------------------------------------------------------------------
    # Episode planning
    # ------------------------------------------------------------------

    async def plan_episode(
        self,
        topic: dict,
        detailed_info: list[dict],
        guest_names: list[str],
    ) -> EpisodePlan:
        """Create a structured episode outline based on deep research."""
        info_text = "\n\n".join(
            f"【搜索角度: {info.get('query', '')}】\n{info.get('answer', '')}"
            for info in detailed_info
        )

        prompt = f"""基于以下信息，请为今天的播客策划一期节目大纲。

【今日话题】
{topic.get('topic', '')}

【选题理由】
{topic.get('reason', '')}

【深度资料】
{info_text}

【参与嘉宾】
{', '.join(guest_names)}

请以JSON格式返回节目大纲（不要包含markdown代码块标记）：
{{
    "topic": "节目主题",
    "summary": "2-3句话播客摘要",
    "opening": "开场白方向（提示你自己怎么开场）",
    "talking_points": [
        "讨论要点1：...",
        "讨论要点2：...",
        "讨论要点3：...",
        "讨论要点4：..."
    ],
    "closing": "结尾总结方向"
}}

要求：
- 讨论要点要有层次感：从"是什么"→"为什么重要"→"不同观点"→"未来展望"
- 每个讨论要点要具体，包含可以引导嘉宾发言的方向
- 控制在4-5个讨论要点，适配5分钟播客"""

        response = await self.think(prompt, temperature=0.7, max_tokens=1500)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            return EpisodePlan(**data)
        except (json.JSONDecodeError, Exception) as exc:
            logger.error(
                "Failed to parse episode plan: %s | raw: %s", exc, response)
            return EpisodePlan(
                topic=topic.get("topic", "AI讨论"),
                summary="关于最新AI话题的深度讨论",
                talking_points=["技术解读", "行业影响", "伦理思考"],
                opening="欢迎来到MindCast",
                closing="感谢收听",
            )

    # ------------------------------------------------------------------
    # Line generation
    # ------------------------------------------------------------------

    async def generate_line(
        self,
        context: list[dict[str, str]],
        instruction: str,
    ) -> DialogueLine:
        """Generate a single host line within the podcast conversation."""
        prompt = f"""【主持人指令】{instruction}

请生成你（{self.name}）在这个位置的发言。

要求：
- 一段自然的口语化发言，50-150字左右
- 按照语音标注规则自然地加入停顿标记 `<#X#>` 和语气词标签
- 保持你ENFJ的主持风格

请以JSON格式返回（不要包含markdown代码块标记）：
{{
    "text": "用于展示的纯净文本（不含标注）",
    "ssml_text": "带语音标注的文本（含 <#X#> 停顿和情感语气词）",
    "emotion": "当前情感状态（如 happy, neutral, excited, thoughtful）"
}}"""

        response = await self.think(prompt, conversation_history=context, temperature=0.85, max_tokens=800)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            return DialogueLine(
                speaker=self.name,
                text=data.get("text", ""),
                ssml_text=data.get("ssml_text", data.get("text", "")),
                emotion=data.get("emotion", "neutral"),
                voice_id=self.persona.voice_id,
            )
        except (json.JSONDecodeError, Exception) as exc:
            logger.error("Failed to parse host line: %s", exc)
            # Fallback: use raw response as text
            return DialogueLine(
                speaker=self.name,
                text=response,
                ssml_text=response,
                emotion="neutral",
                voice_id=self.persona.voice_id,
            )
