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

选择标准——像一个真正的播客主编一样思考：
1. 话题本身有"张力"——存在争议、悖论、意外转折，而不只是又一个"XX发布了XX"
2. 能从多个角度切入深度讨论（技术原理、商业逻辑、社会影响、伦理边界等）
3. 和普通听众的生活有真实关联——通勤路上听了会觉得"哦!原来跟我有关"
4. 不是炒冷饭——优先选有新信息增量的话题

请以JSON格式返回你的选择（不要包含markdown代码块标记）：
{{
    "index": 选中的新闻序号,
    "topic": "提炼的播客话题方向（一句话，要有观点倾向而非纯中性描述）",
    "reason": "选择理由（用你自己的判断讲2-3句话，不要用套话）",
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
    "topic": "节目主题（带有一定观点色彩的标题，像真实播客节目名）",
    "summary": "2-3句话播客摘要，写给听众看的——要让人有点击欲望",
    "opening": "开场白策略（你打算怎么开场来抓住听众注意力——可以是一个反直觉的事实、一个尖锐的问题、或者一个生活化的场景）",
    "talking_points": [
        "讨论要点1：先抛出一个让人意外的事实或数据来破冰",
        "讨论要点2：深入技术原理——但要讲成普通人能懂的白话",
        "讨论要点3：引入一个有争议性的角度，让嘉宾之间产生碰撞",
        "讨论要点4：回到现实——这件事对普通人意味着什么"
    ],
    "closing": "收尾方向——留一个开放性的思考题，而不是大而空的展望"
}}

要求：
- 讨论要点不要写得像论文大纲，要像真人在聊天前"盘"话题的思路
- 每个要点要包含足够具体的信息，让嘉宾有东西可以聊
- 要标注出可能产生观点冲突的地方——碰撞越多越好听
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

    async def decide_need_fresh_search(
        self,
        query: str,
        rag_snippets: list[str],
    ) -> dict:
        """Decide whether to call Tavily for fresher / deeper info.

        Returns a dict:
        {
            "need_fresh_search": bool,
            "reason": str,
            "focus": str
        }
        """
        rag_text = "\n".join(
            f"{i+1}. {snippet[:280]}"
            for i, snippet in enumerate(rag_snippets[:6])
        )

        prompt = f"""你是播客主编，需要判断当前资料是否足够支撑这一搜索角度。

【搜索角度】
{query}

【知识库检索结果（RAG）】
{rag_text or '（暂无）'}

判断规则：
1. 如果RAG内容太少、过旧、信息密度不够，或缺关键事实，返回 need_fresh_search=true
2. 如果RAG已足够支撑该角度讨论，返回 need_fresh_search=false
3. 如果话题明显需要最新动态（如“刚发布/本周/最新进展”），优先返回 true

请严格返回JSON（不要markdown代码块）：
{{
  "need_fresh_search": true 或 false,
  "reason": "一句话说明判断原因",
  "focus": "若需要新搜索，给出一个更聚焦的搜索意图；否则给空字符串"
}}"""

        response = await self.think(prompt, temperature=0.2, max_tokens=400)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            return {
                "need_fresh_search": bool(data.get("need_fresh_search", False)),
                "reason": str(data.get("reason", "")),
                "focus": str(data.get("focus", "")),
            }
        except Exception:
            logger.warning("Failed to parse fresh-search decision JSON: %s", response)
            return {
                "need_fresh_search": len(rag_snippets) < 2,
                "reason": "fallback: rag信息不足时补充搜索",
                "focus": query,
            }

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
- 像在朋友聚会上聊天那样自然——可以口语化、可以断句、可以"嗯"一下再继续
- 不要用"关于这个话题"、"首先我们来看"之类的主持人套话
- 可以穿插你个人的一个小观察或者一个具体的例子
- 如果要追问，像真正好奇那样追问，而不是"那么请问您对此怎么看"
- 按照语音标注规则自然地加入停顿标记 `<#X#>` 和语气词标签

严禁出现：三段式总结、"值得关注"、"让我们拭目以待"、"不可忽视"、否定式排比

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
