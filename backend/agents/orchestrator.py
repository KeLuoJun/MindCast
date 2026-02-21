"""Podcast orchestrator — LangGraph pipeline for complete episode generation."""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.guest import GuestAgent
from backend.agents.host import HostAgent
from backend.agents.personas import (
    GUEST_PERSONAS,
    HOST_FIXED_VOICE_ID,
    VOICE_LIBRARY_BY_GENDER,
)
from backend.config import settings
from backend.knowledge import get_knowledge_base
from backend.knowledge.chroma_kb import (
    BACKGROUND_MATERIAL,
    KNOWLEDGE_SCOPE_GLOBAL,
)
from backend.logging_config import get_episode_file_handler
from backend.models import DetailedInfo, DialogueLine, Episode, EpisodePlan, NewsItem, PersonaConfig
from backend.services.audio_service import AudioService, audio_service
from backend.services.llm_service import LLMService, get_llm_service
from backend.services.news_service import NewsService, get_news_service
from backend.services.run_logger import EpisodeRunLogger
from backend.services.tts_service import TTSService, get_tts_service

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, str], Awaitable[None]] | None


class OrchestratorState(TypedDict, total=False):
    """State that flows through the LangGraph pipeline."""

    episode: Episode
    topic: dict[str, Any]
    detailed_info: list[DetailedInfo]
    plan: EpisodePlan
    dialogue: list[DialogueLine]
    audio_segments: list[tuple[bytes, float]]
    progress: ProgressCallback
    run_logger: EpisodeRunLogger
    rag_context: str
    active_guests: list[GuestAgent]  # Guests for this specific run
    speaker_voice_map: dict[str, str]


class PodcastOrchestrator:
    """End-to-end pipeline: news → topic → script → audio, powered by LangGraph."""

    def __init__(
        self,
        llm: LLMService | None = None,
        news: NewsService | None = None,
        tts: TTSService | None = None,
        audio: AudioService | None = None,
        guest_personas: list[PersonaConfig] | None = None,
    ) -> None:
        self._llm = llm or get_llm_service()
        self._news = news or get_news_service()
        self._tts = tts or get_tts_service()
        self._audio = audio or audio_service

        self.host = HostAgent(self._llm)
        # We'll select guest instances per episode run to control guest count
        guest_configs = guest_personas or GUEST_PERSONAS
        self._guest_pool = {p.name: GuestAgent(
            p, self._llm) for p in guest_configs}
        self._app = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph pipeline once and reuse for every run."""
        graph = StateGraph(OrchestratorState)
        graph.add_node("fetch_news", self._node_fetch_news)
        graph.add_node("select_topic", self._node_select_topic)
        graph.add_node("deep_research", self._node_deep_research)
        graph.add_node("retrieve_rag", self._node_retrieve_rag)
        graph.add_node("plan_episode", self._node_plan_episode)
        graph.add_node("generate_dialogue", self._node_generate_dialogue)
        graph.add_node("generate_article", self._node_generate_article)
        graph.add_node("synthesize_tts", self._node_synthesize_tts)
        graph.add_node("stitch_audio", self._node_stitch_audio)
        graph.add_node("save_episode", self._node_save_episode)

        graph.add_edge(START, "fetch_news")
        graph.add_edge("fetch_news", "select_topic")
        graph.add_edge("select_topic", "deep_research")
        graph.add_edge("deep_research", "retrieve_rag")
        graph.add_edge("retrieve_rag", "plan_episode")
        graph.add_edge("plan_episode", "generate_dialogue")
        graph.add_edge("generate_dialogue", "generate_article")
        graph.add_edge("generate_article", "synthesize_tts")
        graph.add_edge("synthesize_tts", "stitch_audio")
        graph.add_edge("stitch_audio", "save_episode")
        graph.add_edge("save_episode", END)
        return graph

    def _build_active_guests(self, selected_guest_names: list[str] | None = None) -> list[GuestAgent]:
        names = [name.strip() for name in (selected_guest_names or [])
                 if name and name.strip()]
        if names:
            unknown = [name for name in names if name not in self._guest_pool]
            if unknown:
                raise ValueError(f"Unknown guests: {', '.join(unknown)}")
            return [self._guest_pool[name] for name in names]

        num_guests = random.randint(1, 2)
        selected_names = random.sample(
            list(self._guest_pool.keys()), num_guests)
        return [self._guest_pool[name] for name in selected_names]

    async def generate_episode(
        self,
        progress: ProgressCallback = None,
        *,
        topic: str = "",
        selected_guest_names: list[str] | None = None,
    ) -> Episode:
        """Run the complete podcast generation pipeline via LangGraph."""
        active_guests = self._build_active_guests(selected_guest_names)
        selected_names = [guest.persona.name for guest in active_guests]
        speaker_voice_map = self._build_speaker_voice_map(active_guests)

        normalized_topic = (topic or "").strip()
        episode = Episode(guests=selected_names,
                          topic=normalized_topic, title=normalized_topic)
        output_dir = settings.ensure_output_dir()
        run_log = EpisodeRunLogger(output_dir / "logs" / f"{episode.id}.jsonl")
        episode.generation_log_path = str(run_log.log_path)

        # Attach per-episode file handler so all loggers write to the episode log
        ep_handler = get_episode_file_handler(episode.id, output_dir)
        logging.getLogger().addHandler(ep_handler)

        run_log.event(
            "pipeline",
            "episode generation started",
            payload={"episode_id": episode.id, "guests": episode.guests},
        )

        try:
            final_state = await self._app.ainvoke(
                {
                    "episode": episode,
                    "topic": {"topic": normalized_topic} if normalized_topic else {},
                    "detailed_info": [],
                    "dialogue": [],
                    "audio_segments": [],
                    "progress": progress,
                    "run_logger": run_log,
                    "rag_context": "",
                    "active_guests": active_guests,
                    "speaker_voice_map": speaker_voice_map,
                }
            )
            result_episode = final_state["episode"]
            run_log.event(
                "pipeline",
                "episode generation completed",
                status="success",
                payload={
                    "episode_id": result_episode.id,
                    "audio_path": result_episode.audio_path,
                    "duration_seconds": result_episode.duration_seconds,
                    "word_count": result_episode.word_count,
                },
            )
            return result_episode
        except Exception as exc:
            logger.exception("Episode generation failed")
            run_log.exception("pipeline", exc, payload={
                              "episode_id": episode.id})
            raise
        finally:
            self.host.reset_history()
            for g in active_guests:
                g.reset_history()
            # Remove per-episode file handler
            logging.getLogger().removeHandler(ep_handler)
            ep_handler.close()

    async def _emit_progress(
        self,
        state: OrchestratorState,
        stage: str,
        detail: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Report progress to API callback and structured run logger."""
        logger.info("[%s] %s", stage, detail)
        state["run_logger"].event(stage, detail, payload=payload)
        callback = state.get("progress")
        if callback:
            await callback(stage, detail)

    async def _node_fetch_news(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        user_topic = (episode.topic or "").strip()
        await self._emit_progress(state, "news", f"正在获取{'\u300c' + user_topic + '\u300d相关' if user_topic else ''}资讯…")
        news_items = await self._news.get_topic_news(topic=user_topic, max_results=10)
        if not news_items:
            raise RuntimeError("No news items retrieved from Tavily")

        episode.news_sources = news_items
        await self._emit_progress(
            state,
            "news",
            f"获取到{len(news_items)}条资讯",
            payload={"count": len(news_items), "titles": [
                item.title for item in news_items]},
        )
        return {"episode": episode}

    async def _node_select_topic(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]

        if episode.topic.strip():
            user_topic = episode.topic.strip()
            topic = {
                "topic": user_topic,
                "reason": "用户手动选择话题",
                "search_queries": [
                    user_topic,
                    f"{user_topic} 最新进展",
                    f"{user_topic} 行业争议",
                ],
            }
            await self._emit_progress(
                state,
                "topic",
                f"使用用户选择话题: {user_topic}",
                payload=topic,
            )
            return {"episode": episode, "topic": topic}

        await self._emit_progress(state, "topic", "主持人正在选题…")
        recent_topics = self._load_recent_topics(
            limit=20,
            exclude_episode_id=episode.id,
        )
        topic = await self.host.select_topic(
            episode.news_sources,
            recent_topics=recent_topics,
        )
        episode.topic = topic.get("topic", "")
        episode.title = episode.topic
        await self._emit_progress(
            state,
            "topic",
            f"选题完成: {episode.topic}",
            payload={**topic, "recent_topics_count": len(recent_topics)},
        )
        return {"episode": episode, "topic": topic}

    def _load_recent_topics(
        self,
        *,
        limit: int = 20,
        exclude_episode_id: str | None = None,
    ) -> list[str]:
        """Load recent discussed topics from saved episodes for topic de-dup."""
        output_dir: Path = settings.output_dir
        if not output_dir.exists():
            return []

        topics: list[str] = []
        for json_path in sorted(output_dir.glob("*.json"), reverse=True):
            try:
                if exclude_episode_id and json_path.stem == exclude_episode_id:
                    continue
                episode = Episode.load_json(json_path)
                topic = (episode.topic or episode.title or "").strip()
                if topic:
                    topics.append(topic)
                if len(topics) >= limit:
                    break
            except Exception:
                continue
        return topics

    async def _node_deep_research(self, state: OrchestratorState) -> OrchestratorState:
        topic = state["topic"]
        await self._emit_progress(state, "research", "正在深度搜索…")
        search_queries = topic.get("search_queries", [])[:5]
        detailed_info: list[DetailedInfo] = []
        kb = get_knowledge_base()

        for i, query in enumerate(search_queries):
            await self._emit_progress(
                state,
                "research",
                f"深度搜索 ({i + 1}/{len(search_queries)}): {query}",
                payload={"query": query, "index": i +
                         1, "total": len(search_queries)},
            )

            # 1) Retrieve from long-term RAG first
            rag_docs = await kb.query(
                query,
                top_k=4,
                collection=BACKGROUND_MATERIAL,
                scope=KNOWLEDGE_SCOPE_GLOBAL,
            )
            rag_snippets = [d.get("content", "")
                            for d in rag_docs if d.get("content")]

            # 2) Let host agent decide whether fresh web search is needed
            decision = await self.host.decide_need_fresh_search(query, rag_snippets)
            need_fresh_search = bool(decision.get("need_fresh_search", False))
            if not rag_snippets:
                need_fresh_search = True

            if need_fresh_search:
                focus_query = decision.get("focus", "").strip() or query
                info = await self._news.search_detail(focus_query)
                info_source = "tavily"
            else:
                rag_answer = "\n\n".join(
                    f"- {txt[:300]}" for txt in rag_snippets[:4])
                info = DetailedInfo(
                    query=query,
                    answer=f"基于知识库历史资料整理：\n{rag_answer}" if rag_answer else "",
                    results=[],
                )
                info_source = "rag"

            detailed_info.append(info)
            state["run_logger"].event(
                "research",
                "search result captured",
                payload={
                    "query": query,
                    "source": info_source,
                    "need_fresh_search": need_fresh_search,
                    "decision_reason": decision.get("reason", ""),
                    "rag_hit_count": len(rag_docs),
                    "answer": info.answer,
                    "result_count": len(info.results),
                    "result_titles": [item.title for item in info.results],
                },
            )

        await self._emit_progress(
            state,
            "research",
            f"完成{len(detailed_info)}轮深度搜索",
            payload={"query_count": len(detailed_info)},
        )
        return {"detailed_info": detailed_info}

    async def _node_retrieve_rag(self, state: OrchestratorState) -> OrchestratorState:
        """Retrieve relevant knowledge from the RAG database."""
        topic = state["topic"]
        topic_text = topic.get("topic", "")
        if not topic_text:
            return {"rag_context": ""}

        await self._emit_progress(state, "rag", "正在检索知识库…")
        try:
            kb = get_knowledge_base()
            rag_context = await kb.build_rag_context(
                topic_text, top_k_per_collection=3,
            )
            stats = kb.get_collection_stats()
            await self._emit_progress(
                state,
                "rag",
                f"知识库检索完成 (库容量: {stats})",
                payload={"rag_context_len": len(rag_context), "stats": stats},
            )
        except Exception as exc:
            logger.warning("RAG retrieval failed, continuing without: %s", exc)
            rag_context = ""

        return {"rag_context": rag_context}

    async def _node_plan_episode(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        topic = state["topic"]
        detailed_info = state.get("detailed_info", [])
        active_guests = state.get("active_guests", [])

        await self._emit_progress(state, "planning", "主持人正在策划节目大纲…")
        guest_names = [g.persona.name for g in active_guests]
        plan = await self.host.plan_episode(
            topic,
            [info.model_dump() for info in detailed_info],
            guest_names,
        )
        episode.summary = plan.summary

        await self._emit_progress(
            state,
            "planning",
            f"大纲完成: {len(plan.talking_points)}个讨论要点",
            payload=plan.model_dump(),
        )
        return {"episode": episode, "plan": plan}

    async def _node_generate_dialogue(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        plan = state["plan"]
        detailed_info = state.get("detailed_info", [])

        await self._emit_progress(state, "dialogue", "正在生成播客对话…")
        dialogue = await self._generate_dialogue(plan, detailed_info, state)
        episode.dialogue = dialogue
        episode.word_count = sum(len(line.text) for line in dialogue)

        await self._emit_progress(
            state,
            "dialogue",
            f"对话生成完成: {len(dialogue)}条台词, {episode.word_count}字",
            payload={"line_count": len(
                dialogue), "word_count": episode.word_count},
        )
        return {"episode": episode, "dialogue": dialogue}

    async def _node_synthesize_tts(self, state: OrchestratorState) -> OrchestratorState:
        dialogue = state.get("dialogue", [])
        await self._emit_progress(state, "audio", "正在实时合成语音…")
        audio_segments = await self._synthesize_dialogue_segments(
            dialogue,
            progress=lambda detail, payload: self._emit_progress(
                state,
                "audio",
                detail,
                payload=payload,
            ),
            run_logger=state["run_logger"],
        )
        await self._emit_progress(state, "audio", "语音合成全部完成")
        return {"audio_segments": audio_segments}

    async def _node_stitch_audio(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        audio_segments = state.get("audio_segments", [])

        await self._emit_progress(state, "audio", "正在拼接音频…")
        output_dir = settings.ensure_output_dir()
        audio_ext = settings.minimax_audio_format.lower()
        if audio_ext not in {"mp3", "wav"}:
            audio_ext = "wav"

        output_path = output_dir / f"{episode.id}.{audio_ext}"
        duration = await self._audio.stitch_episode(
            audio_segments=audio_segments,
            output_path=str(output_path),
        )
        episode.audio_path = str(output_path)
        episode.duration_seconds = duration

        await self._emit_progress(
            state,
            "audio",
            f"音频拼接完成: {duration:.1f}秒",
            payload={"audio_path": str(output_path),
                     "duration_seconds": duration},
        )
        return {"episode": episode}

    async def _node_generate_article(self, state: OrchestratorState) -> OrchestratorState:
        """Generate a high-quality long-form article based on the episode content."""
        episode = state["episode"]
        plan = state.get("plan")
        detailed_info: list[DetailedInfo] = state.get("detailed_info", [])
        dialogue = state.get("dialogue", [])

        await self._emit_progress(state, "article", "正在撰写本期深度文章…")

        try:
            # Build context from research and dialogue
            research_summary = "\n".join(
                f"【{info.query}】\n{info.answer or ''}\n"
                + "\n".join(
                    f"- {r.title}: {r.content[:200]}"
                    for r in (info.results or [])[:3]
                )
                for info in detailed_info
            )
            talking_points = plan.talking_point_texts() if plan else []
            dialogue_excerpt = "\n".join(
                f"{line.speaker}：{line.text}" for line in dialogue[:40]
            )
            guest_names = "、".join(episode.guests) if episode.guests else "嘉宾"

            system_prompt = f"""你是一位精通科技与社会议题的中文深度内容编辑，擅长将播客讨论提炼为独立成篇的高质量文章。
你的写作风格：
- 观点鲜明、逻辑严密，有自己的判断和立场
- 用具体案例、数据和类比解释复杂概念
- 语言克制有力，不用空洞词汇
- 结构清晰但不生硬，行文流畅自然
- 适合发布在《晚点LatePost》《虎嗅》《36氪》等深度科技媒体

【⛔ 绝对禁止的写作痕迹】
- 三段式"第一……第二……第三"
- "值得注意的是"、"不可忽视"、"此外"、"与此同时"、"综上所述"
- "赋能"、"打造"、"引领"、"助力"、"深耕"
- "让我们拭目以待"、"未来可期"
- 每句话长度接近、节奏单调
- 空洞总结段（要么给新洞察，要么不总结）"""

            user_prompt = f"""本期播客主题：{episode.topic}

【节目梗概】
{episode.summary}

【讨论脉络】
{chr(10).join(f'· {pt}' for pt in talking_points)}

【研究背景资料】
{research_summary[:3000]}

【部分对话精华】
{dialogue_excerpt}

请根据以上内容，以**独立文章**的形式撰写一篇1500-2500字的深度文章。

要求：
1. 文章要能独立成篇，读者无需听播客也能完整理解
2. 不要描述"本期节目讨论了……"——直接切入话题本身
3. 文章结构自由，但逻辑线索清晰：通常包含核心观点引入、多角度分析、现实影响/启示
4. 提炼播客中最有价值的洞见，加入必要的背景知识和你自己的分析判断
5. 参考 {guest_names} 在对话中的核心论点，但以你自己的叙事语言转化，不要像"摘要"或"采访综述"
6. 标题要吸引眼球，能准确传达文章核心角度（可以用副标题补充）
7. 直接输出文章全文（含标题），不要有任何前缀说明

现在开始写作："""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            article_text = await self._llm.chat(
                messages, temperature=0.75, max_tokens=3000
            )
            article_text = (article_text or "").strip()

            episode.article = article_text
            logger.info(
                "Article generated for episode %s (%d chars)",
                episode.id,
                len(article_text),
            )
            await self._emit_progress(
                state,
                "article",
                f"深度文章撰写完成（{len(article_text)} 字）",
                payload={"article_length": len(article_text)},
            )
        except Exception as exc:
            logger.warning("Article generation failed: %s", exc)
            episode.article = ""

        return {"episode": episode}

    async def _node_save_episode(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        output_dir = settings.ensure_output_dir()
        metadata_path = episode.save_json(output_dir)

        # Ingest episode into knowledge base for future RAG retrieval
        try:
            kb = get_knowledge_base()
            await kb.ingest_episode(
                episode_id=episode.id,
                topic=episode.topic,
                summary=episode.summary,
                dialogue_lines=[
                    {"speaker": d.speaker, "text": d.text}
                    for d in episode.dialogue
                ],
                news_sources=[s.model_dump() for s in episode.news_sources],
            )
            logger.info("Episode %s ingested into knowledge base", episode.id)
        except Exception as exc:
            logger.warning("Failed to ingest episode into KB: %s", exc)

        await self._emit_progress(
            state,
            "done",
            f"播客生成完成！ID: {episode.id}",
            payload={
                "episode_id": episode.id,
                "metadata_path": str(metadata_path),
                "log_path": episode.generation_log_path,
            },
        )
        return {"episode": episode}

    async def _generate_dialogue(
        self,
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
        state: OrchestratorState,
    ) -> list[DialogueLine]:
        """Generate the full dialogue script turn by turn with interruption simulation."""
        dialogue: list[DialogueLine] = []
        shared_context: list[dict[str, str]] = []

        rag_context = state.get("rag_context", "")
        bg_info = self._build_background_info(plan, detailed_info, rag_context)
        shared_context.append({"role": "system", "content": bg_info})

        active_guests = state.get("active_guests", [])
        speaker_voice_map = state.get("speaker_voice_map", {})
        guest_map = {g.persona.name: g for g in active_guests}
        guest_names = [g.persona.name for g in active_guests]

        # Helper to append a line and log it
        def _append_line(line: DialogueLine) -> None:
            mapped_voice = speaker_voice_map.get(line.speaker)
            if mapped_voice:
                line.voice_id = mapped_voice
            dialogue.append(line)
            shared_context.append(
                {"role": "assistant", "content": f"[{line.speaker}]: {line.text}"})
            state["run_logger"].event(
                "dialogue",
                "line generated",
                payload={"speaker": line.speaker,
                         "text": line.text, "emotion": line.emotion},
            )

        # --- Opening ---
        # Add the fixed show opening
        fixed_opening_text = "各位好，欢迎来到——『圆桌派』。在这里，我们抛开表面的新闻标题，聊一聊这些热点背后真正值得思考的问题。"
        _append_line(
            DialogueLine(
                speaker=self.host.name,
                text=fixed_opening_text,
                ssml_text=f"{fixed_opening_text}<#1000#>",  # Add a pause
                emotion="happy",
                voice_id=self.host.persona.voice_id
            )
        )

        opening_hint = plan.opening_text()
        trimmed_open = self._trim_shared_context(shared_context)
        opening_line = await self.host.generate_line(
            trimmed_open,
            f"现在是节目开场。请紧接刚才的开场白，用一种轻松自然的方式带出今天的话题「{plan.topic}」，"
            f"顺便介绍{len(guest_names)}位嘉宾：{'、'.join(guest_names)}。"
            f"开场要求：紧接『圆桌派』的基调；别搞『欢迎收听』模板；可用反直觉事实、尖锐问题或生活化场景做钩子；"
            f"可轻微表达你的立场或困惑。{opening_hint}",
        )
        _append_line(opening_line)

        # Track how many interruptions have occurred to avoid overuse
        interruption_count = 0
        max_interruptions = 2  # At most 2 interruptions per episode

        for tp_idx, _ in enumerate(plan.talking_points):
            talking_point = plan.talking_point_text(tp_idx)
            depth_hint = plan.talking_point_depth_hint(tp_idx)
            conflict_setup = plan.talking_point_conflict_setup(tp_idx)
            example_needed = plan.talking_point_example_needed(tp_idx)
            arc_pos = plan.arc_position(tp_idx)
            total_points = len(plan.talking_points)

            await self._emit_progress(
                state,
                "dialogue",
                f"讨论要点 {tp_idx + 1}/{total_points}: {talking_point[:30]}…",
                payload={"talking_point": talking_point, "index": tp_idx + 1},
            )

            # Host introduces the talking point — technique varies by arc position
            # Techniques based on podcast research:
            #   exposition   → anecdote hook / life-scenario opener
            #   rising_action → contrast probe ("before vs now") / challenge assumption
            #   climax        → emotional recall / hypothetical scenario / reveal unexpected_angle
            #   falling_action → synthesize conflict, pivot toward resolution
            if arc_pos == "exposition":
                intro_technique = (
                    f"引入讨论要点：「{talking_point}」。"
                    f"开场用一个生活化场景或反直觉事实做钩子，让听众立刻感到「这和我有关」。"
                    f"然后向{guest_names[0]}抛出第一个问题，要具体，不要泛问「你怎么看」。"
                    f"背景补充方向：{depth_hint or '把这件事的来龙去脉交代清楚'}。"
                )
            elif arc_pos == "rising_action":
                intro_technique = (
                    f"深化讨论：「{talking_point}」。"
                    f"用对比性追问打开空间——可以是「一年前你们行业怎么看这问题？现在变了吗？」"
                    f"或者挑战上一轮的某个假设：「等等，那个前提站得住脚吗？」"
                    f"可能的冲突点：{conflict_setup or '不同利益方对这件事的权重判断完全不同'}。"
                    f"需要的案例或数据：{example_needed or '具体到人、到事的佐证'}。"
                )
            elif arc_pos == "climax":
                unexpected = plan.unexpected_angle or "这件事背后有一个大家没注意到的变量"
                intro_technique = (
                    f"全片高潮时刻——讨论要点：「{talking_point}」。"
                    f"现在抛出今天节目最有冲击力的角度：{unexpected}。"
                    f"可用情感召回法：「带我回到你第一次意识到这个问题的时候，当时发生了什么？」"
                    f"或设定极端假设场景让嘉宾决策，探测价值观真实边界。"
                    f"这里要有张力，不要急着和稀泥——让不同观点的碰撞多发酵一会儿。"
                    f"冲突设计：{conflict_setup or '此处应有明确的立场分叉'}。"
                )
            else:  # falling_action / resolution
                intro_technique = (
                    f"进入收尾阶段：「{talking_point}」。"
                    f"先快速总结刚才分歧的核心：「你们真正的分歧其实是在……」"
                    f"然后追问影响与后果：这些争议对普通人意味着什么？短期vs长期如何？"
                    f"追问方向：{depth_hint or '把讨论落回到听众的真实生活'}。"
                )

            trimmed_ctx = self._trim_shared_context(shared_context)
            host_intro = await self.host.generate_line(
                trimmed_ctx,
                intro_technique + f"\n不要说'接下来我们来讨论'这种过渡套话。",
            )
            _append_line(host_intro)

            # Determine speaking order and which guests speak this round
            order = self._get_speaking_order(tp_idx, guest_names)
            speakers_this_round = order[:2] if tp_idx < len(
                plan.talking_points) - 1 else order

            for sp_idx, guest_name in enumerate(speakers_this_round):
                guest = guest_map[guest_name]

                # --- Interruption simulation ---
                # Decide whether another guest interrupts before this speaker finishes
                should_interrupt = (
                    interruption_count < max_interruptions
                    and sp_idx == 0  # Only interrupt the first speaker of a round
                    and tp_idx > 0  # Don't interrupt in the first topic
                    and len(speakers_this_round) > 1
                    and random.random() < 0.35  # 35% chance of interruption
                )

                if should_interrupt:
                    # The current guest starts speaking but gets interrupted
                    interrupter_name = speakers_this_round[1] if sp_idx == 0 else speakers_this_round[0]
                    interrupter = guest_map[interrupter_name]

                    # First speaker starts (will be cut short)
                    trimmed_intr = self._trim_shared_context(shared_context)
                    start_line = await guest.generate_line(
                        trimmed_intr,
                        f"你刚要回应关于「{talking_point}」的讨论，但你的发言会被{interrupter_name}打断。"
                        f"所以只说前半句话就被截断了——大概20-40字就被打断，句子可以不完整，"
                        f"用「——」或「…」结尾表示被打断。"
                        f"从你的{guest.persona.occupation}视角出发。",
                    )
                    _append_line(start_line)

                    # Interrupter cuts in
                    trimmed_intr2 = self._trim_shared_context(shared_context)
                    interrupt_line = await interrupter.generate_line(
                        trimmed_intr2,
                        f"你忍不住打断了{guest_name}的发言！可能因为你太想反驳、太兴奋，"
                        f"或突然想到关键点。请用自然口语切入（如『不好意思打断一下』），"
                        f"然后在40-80字内快速给出核心观点。"
                        f"关于「{talking_point}」，从你的{interrupter.persona.occupation}角度出发。",
                    )
                    _append_line(interrupt_line)

                    # Original speaker responds / continues
                    trimmed_intr3 = self._trim_shared_context(shared_context)
                    resume_line = await guest.generate_line(
                        trimmed_intr3,
                        f"你被{interrupter_name}打断了。现在你可以接着说或者回应ta的观点。"
                        f"可以表现出被打断的反应——笑着说'行行行让你先说完'、"
                        f"'你这么一说我倒想起来了'、或者直接接上'对对对但是我要说的是'。",
                    )
                    _append_line(resume_line)

                    interruption_count += 1
                    state["run_logger"].event(
                        "dialogue",
                        "interruption occurred",
                        payload={
                            "interrupted_by": interrupter_name,
                            "interrupted_speaker": guest_name,
                            "talking_point": talking_point,
                        },
                    )
                    # Skip the interrupter's normal turn since they already spoke
                    continue

                # Normal guest turn
                # Build a more contextual instruction based on position and arc
                arc_guidance = {
                    "exposition": "先把你在这方面的第一手观察讲清楚，用一个具体案例打底。",
                    "rising_action": "在前一位嘉宾的基础上加新信息量，不要重复，要有增量或转折。",
                    "climax": "这是全片最重要的时刻，把你最核心的判断说出来，不要留水分。敢于暴露真实困惑或反直觉立场。",
                    "falling_action": "回到你最在意的那个核心论点，给出一个可操作的具体判断。",
                }.get(arc_pos, "")

                example_prompt = f"背景资料里提到需要这类案例或数据：{example_needed}。" if example_needed else ""
                depth_prompt = f"深挖方向：{depth_hint}。" if depth_hint else ""

                if sp_idx == 0:
                    instruction = (
                        f"回应主持人关于「{talking_point}」的讨论。"
                        f"从你{guest.persona.occupation}的真实经验出发——"
                        f"最好能举一个你亲历或具体了解的案例，而不是泛泛而谈。"
                        f"你的立场倾向是：{guest.persona.stance_bias or '保持审慎但有判断'}。"
                        f"{depth_prompt}{example_prompt}{arc_guidance}"
                    )
                else:
                    prev_speaker = speakers_this_round[sp_idx - 1]
                    prev_guest = guest_map[prev_speaker]
                    stance_diff_hint = (
                        "立场差异明显，建议正面交锋，不要绕圈子"
                        if (guest.persona.stance_bias or "") != (prev_guest.persona.stance_bias or "")
                        else "立场可能接近——找到你们的分歧点，或者引入新的对立维度"
                    )
                    instruction = (
                        f"你听了{prev_speaker}关于「{talking_point}」的观点。"
                        f"你可以接着ta的话往深了聊，也可以反驳。"
                        f"重点是：给出有新增信息量的回应，不要重复别人的意思。"
                        f"从你{guest.persona.occupation}视角出发。"
                        f"你的立场：{guest.persona.stance_bias or '保持审慎但有判断'}。"
                        f"与{prev_speaker}的立场差异：{stance_diff_hint}。"
                        f"{depth_prompt}{example_prompt}{arc_guidance}"
                    )

                trimmed_ctx_guest = self._trim_shared_context(shared_context)
                guest_line = await guest.generate_line(trimmed_ctx_guest, instruction)
                _append_line(guest_line)

            # Host follow-up / transition
            if tp_idx < len(plan.talking_points) - 1:
                next_talking_point = plan.talking_point_text(tp_idx + 1)
                next_arc = plan.arc_position(tp_idx + 1)
                # Vary follow-up style by upcoming arc position
                if next_arc == "climax":
                    followup_style = (
                        f"先快速点出刚才讨论的核心分歧：「你们真正不同的地方是……」。"
                        f"然后用一个尖锐问题引出「{next_talking_point}」——这是今天最关键的问题，"
                        f"预告一下它的颠覆性，让听众想继续听。"
                    )
                elif next_arc == "falling_action":
                    followup_style = (
                        f"对刚才的讨论做一个「不总结的提炼」——点出最重要的一个洞见，"
                        f"然后自然引向「{next_talking_point}」，把讨论的余温带进去。"
                    )
                else:
                    followup_style = (
                        f"对嘉宾刚才的观点做一个简短、有态度的回应。"
                        f"可以同意并补充、也可以质疑并追问，或点出核心分歧。"
                        f"然后自然过渡到下一个讨论方向「{next_talking_point}」，"
                        f"不要用'接下来'、'让我们转向'这类套话。"
                    )
                trimmed_followup = self._trim_shared_context(shared_context)
                followup = await self.host.generate_line(trimmed_followup, followup_style)
                _append_line(followup)

            current_words = sum(len(line.text) for line in dialogue)
            if current_words >= settings.target_word_count_max:
                logger.info(
                    "Reached target word count (%d), wrapping up.", current_words)
                state["run_logger"].event(
                    "dialogue",
                    "target word count reached",
                    payload={"current_words": current_words,
                             "target_max": settings.target_word_count_max},
                )
                break

        # --- Pre-closing: each guest gives a brief final take ---
        # This mirrors the "Change Point" technique from Sawatsky: ask each person
        # for their single most important changed perspective from this conversation.
        if guest_names:
            trimmed_pretake = self._trim_shared_context(shared_context)
            host_pretake = await self.host.generate_line(
                trimmed_pretake,
                f"节目即将结束，请每位嘉宾说一句话——不是总结，而是：今天这个讨论里，"
                f"有没有一个让你改变了想法的时刻，或者一个你带走的具体问题？"
                f"语气要自然，像是朋友聊完想问的那句话。先向{guest_names[0]}抛出。",
            )
            _append_line(host_pretake)

            for final_guest_name in guest_names:
                final_guest = guest_map[final_guest_name]
                trimmed_final = self._trim_shared_context(shared_context)
                final_line = await final_guest.generate_line(
                    trimmed_final,
                    f"节目将要结束了。用一到两句话说一个「变革点」——今天的讨论里"
                    f"有没有让你改变看法的时刻？或者你带走的一个还没想清楚的问题？"
                    f"要真实、具体，不要做总结发言，不要说'感谢主持人'之类的套话。"
                    f"体现你{final_guest.persona.occupation}的独特视角。",
                )
                _append_line(final_line)

        # --- Closing ---
        closing_hint = plan.closing_text()
        trimmed_close = self._trim_shared_context(shared_context)
        closing_line = await self.host.generate_line(
            trimmed_close,
            f"节目收尾。不要做长篇总结，也不要说'让我们拭目以待'之类的套话。"
            f"分享一个你在这次讨论后的真实感受、困惑或态度变化，"
            f"简短感谢嘉宾，留一个具体开放问题给听众思考。{closing_hint}",
        )
        _append_line(closing_line)

        return dialogue

    async def synthesize_episode_from_script(
        self,
        *,
        title: str,
        topic: str,
        summary: str,
        guests: list[str],
        dialogue: list[DialogueLine],
        news_sources: list[dict[str, Any]] | None = None,
        progress: ProgressCallback = None,
    ) -> Episode:
        """Create an episode from a prepared/edited script and synthesize audio."""
        episode = Episode(
            title=title or topic,
            topic=topic or title,
            summary=summary,
            guests=guests,
            dialogue=dialogue,
            news_sources=[NewsItem.model_validate(item)
                          for item in (news_sources or [])],
        )
        episode.word_count = sum(len(line.text) for line in dialogue)

        output_dir = settings.ensure_output_dir()
        run_log = EpisodeRunLogger(output_dir / "logs" / f"{episode.id}.jsonl")
        episode.generation_log_path = str(run_log.log_path)

        ep_handler = get_episode_file_handler(episode.id, output_dir)
        logging.getLogger().addHandler(ep_handler)

        async def _emit(stage: str, detail: str, payload: dict[str, Any] | None = None):
            logger.info("[%s] %s", stage, detail)
            run_log.event(stage, detail, payload=payload)
            if progress:
                await progress(stage, detail)

        try:
            speaker_voice_map = self._build_speaker_voice_map(
                self._build_active_guests(guests))
            for line in episode.dialogue:
                if line.speaker in speaker_voice_map:
                    line.voice_id = speaker_voice_map[line.speaker]
                elif not line.voice_id:
                    line.voice_id = HOST_FIXED_VOICE_ID
                if not line.ssml_text:
                    line.ssml_text = line.text

            await _emit("audio", "正在实时合成语音…")
            audio_segments = await self._synthesize_dialogue_segments(
                episode.dialogue,
                progress=lambda detail, payload: _emit(
                    "audio", detail, payload),
                run_logger=run_log,
            )

            await _emit("audio", "正在拼接音频…")
            audio_ext = settings.minimax_audio_format.lower()
            if audio_ext not in {"mp3", "wav"}:
                audio_ext = "wav"
            output_path = output_dir / f"{episode.id}.{audio_ext}"
            duration = await self._audio.stitch_episode(
                audio_segments=audio_segments,
                output_path=str(output_path),
            )
            episode.audio_path = str(output_path)
            episode.duration_seconds = duration

            metadata_path = episode.save_json(output_dir)
            await _emit(
                "done",
                f"播客生成完成！ID: {episode.id}",
                payload={
                    "episode_id": episode.id,
                    "metadata_path": str(metadata_path),
                    "audio_path": str(output_path),
                    "duration_seconds": duration,
                },
            )
            return episode
        finally:
            logging.getLogger().removeHandler(ep_handler)
            ep_handler.close()

    async def _synthesize_dialogue_segments(
        self,
        dialogue: list[DialogueLine],
        *,
        progress: Callable[[str, dict[str, Any]], Awaitable[None]],
        run_logger: EpisodeRunLogger,
        max_concurrency: int = 4,
    ) -> list[tuple[bytes, float]]:
        """Synthesize dialogue into audio segments concurrently while preserving order."""
        if not dialogue:
            return []

        semaphore = asyncio.Semaphore(max_concurrency)
        ordered_segments: list[tuple[bytes, float]
                               | None] = [None] * len(dialogue)

        async def _worker(index: int, line: DialogueLine) -> tuple[int, DialogueLine, bytes]:
            async with semaphore:
                audio_bytes = await self._tts.synthesize(
                    text=line.ssml_text,
                    voice_id=line.voice_id,
                    emotion=line.emotion,
                )
                return index, line, audio_bytes

        tasks = [
            asyncio.create_task(_worker(index, line))
            for index, line in enumerate(dialogue)
        ]

        done_count = 0
        total = len(tasks)
        try:
            for done in asyncio.as_completed(tasks):
                index, line, audio_bytes = await done
                ordered_segments[index] = (audio_bytes, line.pause_after)
                done_count += 1
                await progress(
                    f"语音合成 ({done_count}/{total}): {line.speaker}",
                    {
                        "index": index + 1,
                        "speaker": line.speaker,
                        "emotion": line.emotion,
                        "text_len": len(line.text),
                        "bytes": len(audio_bytes),
                    },
                )
                run_logger.event(
                    "tts",
                    "tts segment generated",
                    payload={
                        "index": index + 1,
                        "speaker": line.speaker,
                        "bytes": len(audio_bytes),
                        "pause_after": line.pause_after,
                    },
                )
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()

        return [segment for segment in ordered_segments if segment is not None]

    def _build_speaker_voice_map(self, active_guests: list[GuestAgent]) -> dict[str, str]:
        """Build voice mapping for one episode run: fixed host + random guests."""
        voice_map = {self.host.name: HOST_FIXED_VOICE_ID}
        used_by_gender: dict[Any, set[str]] = {
            gender: set() for gender in VOICE_LIBRARY_BY_GENDER
        }
        used_by_gender[self.host.persona.gender].add(HOST_FIXED_VOICE_ID)

        for guest in active_guests:
            pool = VOICE_LIBRARY_BY_GENDER.get(guest.persona.gender, [])
            if not pool:
                voice_map[guest.persona.name] = guest.persona.voice_id
                continue
            available = [
                vid for vid in pool if vid not in used_by_gender[guest.persona.gender]]
            chosen = random.choice(available or pool)
            used_by_gender[guest.persona.gender].add(chosen)
            voice_map[guest.persona.name] = chosen
        return voice_map

    @staticmethod
    def _build_background_info(
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
        rag_context: str = "",
    ) -> str:
        """Compile background research + RAG into an E-type structured brief for agents.

        E-type structure: Current State → How We Got Here → Where This Leads.
        This mirrors best-practice used by editors like 'The Daily' to anchor narrative
        in the present, provide historical depth, then open future possibility.
        """
        lines = [
            "=" * 60,
            f"【本期播客话题】{plan.topic}",
            f"【节目摘要】{plan.summary}",
            "",
        ]

        # --- Layer 1: Current state (news anchor — "what's happening NOW") ---
        lines.append("【当前状况——新闻锚点】")
        for info in detailed_info[:2]:
            if info.answer:
                lines.append(f"  {info.answer[:400]}")
            for r in info.results[:1]:
                lines.append(f"  · {r.title}: {r.content[:250]}")
        lines.append("")

        # --- Layer 2: Historical context ("how we got here") ---
        historical_items = detailed_info[2:4] if len(detailed_info) > 2 else []
        if historical_items:
            lines.append("【历史脉络——这是怎么形成的】")
            for info in historical_items:
                if info.answer:
                    lines.append(f"  {info.answer[:400]}")
                for r in info.results[:1]:
                    lines.append(f"  · {r.title}: {r.content[:250]}")
            lines.append("")

        # --- Layer 3: Forward implications ("where this leads") ---
        forward_items = detailed_info[4:] if len(detailed_info) > 4 else []
        if forward_items:
            lines.append("【前赋与影响——可能的多种未来】")
            for info in forward_items:
                if info.answer:
                    lines.append(f"  {info.answer[:400]}")
                for r in info.results[:1]:
                    lines.append(f"  · {r.title}: {r.content[:250]}")
            lines.append("")

        # --- Full research archive (for fact/data lookups) ---
        lines.append("【全量搜索资料（可引用事实、数据、案例）】")
        for info in detailed_info:
            lines.append(f"--- 搜索: {info.query} ---")
            if info.answer:
                lines.append(info.answer[:300])
            for result in info.results[:2]:
                lines.append(f"  · {result.title}: {result.content[:200]}")
        lines.append("")

        # --- RAG: past episodes, expert opinions ---
        if rag_context:
            lines.append("【知识库（历期节目观点、专家评论、事实核查）】")
            lines.append(rag_context[:1500])
            lines.append("")

        # --- Key reminders for agents ---
        lines.append("【讨论要点提醒】" + " | ".join(plan.talking_point_texts()))
        lines.append("【反直觉角度】" + (plan.unexpected_angle or "暂无"))
        lines.append("=" * 60)

        return "\n".join(lines)

    @staticmethod
    def _trim_shared_context(
        ctx: list[dict],
        max_turns: int = 16,
    ) -> list[dict]:
        """Maintain a sliding window over shared conversation context.

        Retains ALL system messages plus the most recent max_turns
        non-system messages. This prevents ever-growing context from
        degrading quality or exceeding token budgets.
        """
        if not ctx:
            return ctx
        system_msgs = [m for m in ctx if m.get("role") == "system"]
        non_system = [m for m in ctx if m.get("role") != "system"]
        if len(non_system) <= max_turns:
            return ctx
        return system_msgs + non_system[-max_turns:]

    @staticmethod
    def _get_speaking_order(round_idx: int, guest_names: list[str]) -> list[str]:
        """Rotate which guest speaks first each round."""
        n = len(guest_names)
        if n == 0:
            return []
        start = round_idx % n
        return guest_names[start:] + guest_names[:start]
