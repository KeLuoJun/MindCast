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
        Optional keys: ``conflict_points``, ``angle_hint``.
        """
        news_summary = "\n".join(
            f"{i+1}. 【{item.title}】{item.content[:200]}"
            for i, item in enumerate(news_list)
        )

        prompt = f"""以下是今天获取到的{len(news_list)}条AI相关资讯：

{news_summary}

请你作为播客主持人，从中挑选**1个最具讨论价值的方向**来做今天这期播客。

【选择标准——像一个真正的播客主编一样思考】

一、话题张力评估
- 是否存在争议、悖论、意外转折？不要选"XX发布了XX"这种单向信息
- 能否形成至少两种不同立场的碰撞？
- 是否有反直觉角度可挖？

二、深度讨论空间
- 是否支持多角度切入：技术原理、商业逻辑、社会影响、伦理边界、历史脉络
- 能否形成追问链条：表层现象 → 深层原因 → 外延影响

三、听众关联度
- 和普通听众生活有真实关联，听完会觉得"原来跟我有关"
- 能否给出生活化类比，解释复杂概念

四、信息增量
- 优先有新信息或新解释框架的话题，避免炒冷饭

请以JSON格式返回你的选择（不要包含markdown代码块标记）：
{{
    "index": 选中的新闻序号,
    "topic": "提炼的播客话题方向（一句话，要有观点倾向，可以是问题或判断句）",
    "reason": "选择理由（2-3句话，说明为什么值得聊、碰撞空间在哪）",
    "conflict_points": ["可能的立场冲突点1", "冲突点2"],
    "search_queries": ["后续深度搜索关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
    "angle_hint": "建议讨论切入角度（如：伦理切入 / 历史对比切入）"
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
                "conflict_points": ["技术推进与社会代价之间的冲突"],
                "search_queries": [news_list[0].title] if news_list else ["AI最新动态"],
                "angle_hint": "从普通用户受影响最明显的场景切入",
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

        conflict_points = topic.get("conflict_points", [])
        if isinstance(conflict_points, str):
            conflict_points = [conflict_points]

        prompt = f"""基于以下信息，请为今天的播客策划一期节目大纲。
【今日话题】
{topic.get('topic', '')}

【选题理由】
{topic.get('reason', '')}

【可能的冲突点】
{'; '.join(conflict_points)}

【建议切入角度】
{topic.get('angle_hint', '')}

【深度资料】
{info_text}

【参与嘉宾】
{', '.join(guest_names)}

请以JSON格式返回节目大纲（不要包含markdown代码块标记）：
{{
    "topic": "节目主题（带观点色彩的标题，像真实播客名）",
    "summary": "2-3句话播客摘要，要有点击欲望，可包含反直觉预告",
    "opening": {{
        "hook": "开场钩子（反直觉事实/尖锐问题/生活化场景）",
        "stance_hint": "主持人在这部分的态度引导"
    }},
    "talking_points": [
        {{
            "point": "讨论要点1：内容说明",
            "depth_hint": "追问挖掘方向（现象->原因->影响）",
            "conflict_setup": "冲突引导（如何让嘉宾产生观点碰撞）",
            "example_needed": "需要穿插的案例或数据"
        }}
    ],
    "closing": {{
        "open_question": "留一个具体开放问题",
        "host_takeaway": "主持人真实感受"
    }}
}}

要求：
- 讨论要点不要写成论文提纲，要像真人聊天前盘话题
- 每个要点都要可落地、可追问、可反驳
- 控制在4-5个讨论要点，适配5分钟播客
- 整体有推进感：现象 → 原因 → 影响 → 判断"""

        response = await self.think(prompt, temperature=0.7, max_tokens=1500)

        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
            if cleaned.endswith("```"):
                cleaned = cleaned.rsplit("```", 1)[0]
            cleaned = cleaned.strip()
            data = json.loads(cleaned)
            normalized = self._normalize_episode_plan_payload(data)
            return EpisodePlan(**normalized)
        except (json.JSONDecodeError, Exception) as exc:
            logger.error(
                "Failed to parse episode plan: %s | raw: %s", exc, response)
            return EpisodePlan(
                topic=topic.get("topic", "AI讨论"),
                summary="关于最新AI话题的深度讨论",
                talking_points=[
                    {"point": "现象层：发生了什么", "depth_hint": "关键事实是什么",
                        "conflict_setup": "乐观与谨慎视角", "example_needed": "最近案例"},
                    {"point": "原因层：为什么发生", "depth_hint": "底层驱动因素",
                        "conflict_setup": "技术与商业主因之争", "example_needed": "对比数据"},
                    {"point": "影响层：对普通人意味着什么", "depth_hint": "短期与长期影响",
                        "conflict_setup": "效率与公平平衡", "example_needed": "生活化场景"},
                ],
                opening={"hook": "一个反直觉开场", "stance_hint": "主持人保持审慎乐观"},
                closing={"open_question": "这个趋势会把我们带向哪里？",
                         "host_takeaway": "讨论后更清楚分歧边界"},
            )

    @staticmethod
    def _normalize_episode_plan_payload(data: dict) -> dict:
        opening_raw = data.get("opening", "")
        if isinstance(opening_raw, dict):
            opening = {
                "hook": str(opening_raw.get("hook", "")).strip(),
                "stance_hint": str(opening_raw.get("stance_hint", "")).strip(),
            }
        else:
            opening = str(opening_raw).strip()

        closing_raw = data.get("closing", "")
        if isinstance(closing_raw, dict):
            closing = {
                "open_question": str(closing_raw.get("open_question", "")).strip(),
                "host_takeaway": str(closing_raw.get("host_takeaway", "")).strip(),
            }
        else:
            closing = str(closing_raw).strip()

        talking_points_raw = data.get("talking_points", [])
        normalized_points: list[str | dict] = []
        if isinstance(talking_points_raw, list):
            for item in talking_points_raw:
                if isinstance(item, dict):
                    normalized_points.append(
                        {
                            "point": str(item.get("point", "")).strip(),
                            "depth_hint": str(item.get("depth_hint", "")).strip(),
                            "conflict_setup": str(item.get("conflict_setup", "")).strip(),
                            "example_needed": str(item.get("example_needed", "")).strip(),
                        }
                    )
                else:
                    normalized_points.append(str(item).strip())

        if not normalized_points:
            normalized_points = ["技术解读", "行业影响", "伦理思考"]

        key_questions = data.get("key_questions", [])
        if not isinstance(key_questions, list):
            key_questions = [str(key_questions)] if key_questions else []

        return {
            "topic": str(data.get("topic", "AI讨论")).strip() or "AI讨论",
            "summary": str(data.get("summary", "关于最新AI话题的深度讨论")).strip() or "关于最新AI话题的深度讨论",
            "opening": opening,
            "talking_points": normalized_points,
            "key_questions": [str(q).strip() for q in key_questions if str(q).strip()],
            "unexpected_angle": str(data.get("unexpected_angle", "")).strip(),
            "closing": closing,
        }

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
            logger.warning(
                "Failed to parse fresh-search decision JSON: %s", response)
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

【发言要求】
一、基础
- 一段自然口语化发言，50-150字左右
- 像朋友聊天：可断句、可犹豫、可小幅情绪起伏
- 不要用"关于这个话题"、"首先我们来看"这类主持人套话

二、深度引导
- 追问要往深里挖，不止停留在表面态度
- 可挑战假设："如果前提变了，结论还成立吗？"
- 可总结分歧："你们核心分歧其实在X"

三、立场表达
- 可以穿插你个人观察或具体例子
- 可以表达倾向或困惑，不要假装中立

四、语音标注
- 自然加入 `<#X#>` 停顿和语气词标签

严禁出现：三段式总结、"值得关注"、"让我们拭目以待"、"不可忽视"、否定式排比

请以JSON格式返回（不要包含markdown代码块标记）：
{{
    "text": "用于展示的纯净文本（不含标注）",
    "ssml_text": "带语音标注的文本（含 <#X#> 停顿和情感语气词）",
    "emotion": "当前情感状态（如 happy, neutral, excited, thoughtful, skeptical, curious）",
    "intent": "发言意图（如 question, challenge, summarize, transition）"
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
