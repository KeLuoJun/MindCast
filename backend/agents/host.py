"""Host agent — topic selection, episode planning, and line generation."""

from __future__ import annotations

import json
import logging
import re

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

    async def select_topic(
        self,
        news_list: list[NewsItem],
        *,
        recent_topics: list[str] | None = None,
    ) -> dict:
        """Pick the most compelling topic direction from a list of news items.

        Returns a dict with keys: ``index``, ``topic``, ``reason``, ``search_queries``.
        Optional keys: ``conflict_points``, ``angle_hint``.
        """
        recent_topics = [t.strip()
                         for t in (recent_topics or []) if t and t.strip()]
        news_summary = "\n".join(
            f"{i+1}. 【{item.title}】{item.content[:200]}"
            for i, item in enumerate(news_list)
        )
        recent_topics_block = "\n".join(
            f"- {topic}" for topic in recent_topics[:20]
        ) or "（暂无往期话题）"

        prompt = f"""以下是今天获取到的{len(news_list)}条相关资讯：

{news_summary}

【往期已聊过的话题（必须规避重复）】
{recent_topics_block}

请你作为播客主持人，从中挑选**1个最具讨论价值的方向**来做今天这期播客。

【选择标准——像一个真正的播客主编一样思考】

一、话题张力评估
- 是否存在争议、悖论、意外转折？不要选"XX发布了XX"这种单向信息
- 能否形成至少两种不同立场的碰撞？
- 是否有反直觉角度可挖？

二、深度讨论空间（弗赖塔格金字塔式结构检验）
- 是否支持多角度切入：技术原理、商业逻辑、社会影响、伦理边界、历史脉络
- 能否形成追问链条：表层现象 → 深层原因 → 外延影响
- 是否能构建"轶事+反思"交替节奏

三、听众关联度
- 和普通听众生活有真实关联，听完会觉得"原来跟我有关"
- 能否给出生活化类比，解释复杂概念

四、信息增量
- 优先有新信息或新解释框架的话题，避免炒冷饭

五、去重硬约束（必须满足）
- 你选择的topic不能与【往期已聊过的话题】语义重复

- 如候选内容与往期高度重合，必须换一个更新颖的角度或换一条资讯

请以JSON格式返回你的选择（不要包含markdown代码块标记）：
{{
    "index": 选中的新闻序号,
    "topic": "提炼的播客话题方向（一句话，要有观点倾向，可以是问题或判断句）",
    "reason": "选择理由（2-3句话，说明为什么值得聊、碰撞空间在哪）",
    "conflict_points": ["可能的立场冲突点1", "冲突点2"],
    "search_queries": ["后续深度搜索关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
    "angle_hint": "建议讨论切入角度（如：伦理切入 / 历史对比切入 / 生活化类比切入）"
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
            selected = json.loads(cleaned)

            selected_topic = str(selected.get("topic", "")).strip()
            if self._is_topic_repetitive(selected_topic, recent_topics):
                logger.info(
                    "Selected topic appears repetitive, switching to fallback topic. topic=%s",
                    selected_topic,
                )
                return self._fallback_non_repetitive_topic(news_list, recent_topics)
            return selected
        except json.JSONDecodeError:
            logger.error("Failed to parse topic selection JSON: %s", response)
            return self._fallback_non_repetitive_topic(news_list, recent_topics)

    @staticmethod
    def _topic_tokens(text: str) -> set[str]:
        raw_tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+", (text or "").lower())
        return {t for t in raw_tokens if len(t) >= 2}

    @classmethod
    def _topic_similarity(cls, left: str, right: str) -> float:
        left_tokens = cls._topic_tokens(left)
        right_tokens = cls._topic_tokens(right)
        if not left_tokens or not right_tokens:
            return 0.0
        inter = left_tokens & right_tokens
        union = left_tokens | right_tokens
        return len(inter) / len(union)

    @classmethod
    def _is_topic_repetitive(cls, topic: str, recent_topics: list[str]) -> bool:
        normalized = (topic or "").lower()
        if not normalized.strip() or not recent_topics:
            return False

        for old_topic in recent_topics:
            old_norm = old_topic.lower()
            if normalized == old_norm:
                return True
            if cls._topic_similarity(topic, old_topic) >= 0.42:
                return True
        return False

    def _fallback_non_repetitive_topic(
        self,
        news_list: list[NewsItem],
        recent_topics: list[str],
    ) -> dict:
        for i, item in enumerate(news_list, start=1):
            if not self._is_topic_repetitive(item.title, recent_topics):
                return {
                    "index": i,
                    "topic": item.title,
                    "reason": "基于往期去重策略，选择与历史讨论重复度更低的资讯方向。",
                    "conflict_points": ["新技术价值与落地成本如何平衡"],
                    "search_queries": [item.title],
                    "angle_hint": "从新增信息和用户真实影响切入",
                }

        # If all today's titles look similar, still return one but force a fresh angle
        fallback_title = news_list[0].title if news_list else "今日热点话题"
        return {
            "index": 1,
            "topic": f"{fallback_title}：这次真正的新变量是什么？",
            "reason": '今日资讯与历史主题相似，改为聚焦"新增变量"的差异化讨论角度。',
            "conflict_points": ["增量是真突破还是叙事包装"],
            "search_queries": [fallback_title, "新增变量", "落地影响"],
            "angle_hint": "不复述已知信息，专注比较新旧变化与外溢影响",
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
            "example_needed": "需要穿插的具体案例或数据（越具体越好）"
        }}
    ],
    "unexpected_angle": "全节目最大的反直觉角度：一个听众没想到的视角或结论，在高潮时刻揭示",
    "closing": {{
        "open_question": "留一个具体开放问题（不是泛问'未来会怎样'，要落到具体细节）",
        "host_takeaway": "主持人真实感受——可以是还没想通的困惑，比总结更有力"
    }}
}}

要求：
- 讨论要点不要写成论文提纲，要像真人聊天前盘话题
- 每个要点都要可落地、可追问、可反驳——"这个点赵明远会反对什么？苏婉清怎么讲？"
- 控制在4-5个讨论要点，适配5分钟播客
- 整体遵循弗赖塔格金字塔：背景铺垫（交代what）→ 激发事件（why now）→ 发展上升 → 首席洞见高潮（最反直觉的那个点）→ 后果分析
- 每个要点安排"轶事+反思"交替节奏：先有生动事实/案例（轶事），再有深层意义提炼（反思）
- 嘉宾的不同专业背景应在不同讨论要点中发挥各自优势：技术、商业、人文各有主场
- `example_needed` 字段极其重要：给出具体的人名、事件、数字，让嘉宾有血有肉可讲
- `unexpected_angle` 必须是真正反直觉的——不是"AI会影响就业"这种人人都知道的话"""

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
                topic=topic.get("topic", "深度讨论"),
                summary="关于最新话题的深度圆桌讨论",
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
                    point_text = str(item.get("point", "")).strip()
                    if point_text:
                        normalized_points.append(
                            {
                                "point": point_text,
                                "depth_hint": str(item.get("depth_hint", "")).strip(),
                                "conflict_setup": str(item.get("conflict_setup", "")).strip(),
                                "example_needed": str(item.get("example_needed", "")).strip(),
                            }
                        )
                else:
                    text_item = str(item).strip()
                    if text_item:
                        normalized_points.append(text_item)

        if not normalized_points:
            normalized_points = ["现象解读", "深层原因", "影响与展望"]
        elif len(normalized_points) > 5:
            normalized_points = normalized_points[:5]

        if len(normalized_points) < 3:
            fallback_points = ["现象解读", "深层原因", "影响与展望"]
            for fb in fallback_points:
                if len(normalized_points) >= 3:
                    break
                normalized_points.append(fb)

        key_questions = data.get("key_questions", [])
        if not isinstance(key_questions, list):
            key_questions = [str(key_questions)] if key_questions else []

        unexpected_angle = str(data.get("unexpected_angle", "")).strip()
        if not unexpected_angle:
            unexpected_angle = "真正关键的变化往往不在技术本身，而在它如何重排成本、权力与责任"

        return {
            "topic": str(data.get("topic", "深度讨论")).strip() or "深度讨论",
            "summary": str(data.get("summary", "关于最新话题的深度圆桌讨论")).strip() or "关于最新话题的深度圆桌讨论",
            "opening": opening,
            "talking_points": normalized_points,
            "key_questions": [str(q).strip() for q in key_questions if str(q).strip()],
            "unexpected_angle": unexpected_angle,
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
