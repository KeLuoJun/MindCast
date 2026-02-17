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
        graph.add_node("synthesize_tts", self._node_synthesize_tts)
        graph.add_node("stitch_audio", self._node_stitch_audio)
        graph.add_node("save_episode", self._node_save_episode)

        graph.add_edge(START, "fetch_news")
        graph.add_edge("fetch_news", "select_topic")
        graph.add_edge("select_topic", "deep_research")
        graph.add_edge("deep_research", "retrieve_rag")
        graph.add_edge("retrieve_rag", "plan_episode")
        graph.add_edge("plan_episode", "generate_dialogue")
        graph.add_edge("generate_dialogue", "synthesize_tts")
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
        await self._emit_progress(state, "news", "正在获取AI资讯…")
        news_items = await self._news.get_daily_ai_news(max_results=10)
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
        fixed_opening_text = "各位好，欢迎来到——『AI圆桌派』。在这里，我们撇开那些干巴巴的代码，只聊聊这股席卷全球的AI浪潮里，最真诚的人性与分歧。"
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
        opening_line = await self.host.generate_line(
            shared_context,
            f"现在是节目开场。请紧接刚才的开场白，用一种轻松自然的方式带出今天的话题「{plan.topic}」，"
            f"顺便介绍{len(guest_names)}位嘉宾：{'、'.join(guest_names)}。"
            f"开场要求：紧接『AI圆桌派』的基调；别搞『欢迎收听』模板；可用反直觉事实、尖锐问题或生活化场景做钩子；"
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
            await self._emit_progress(
                state,
                "dialogue",
                f"讨论要点 {tp_idx + 1}/{len(plan.talking_points)}: {talking_point[:30]}…",
                payload={"talking_point": talking_point, "index": tp_idx + 1},
            )

            # Host introduces the talking point
            host_intro = await self.host.generate_line(
                shared_context,
                f"引入讨论要点：「{talking_point}」。"
                f"可以向某位嘉宾抛出具体问题，或用意外事实/数据开场，或给一个假设场景让对方判断。"
                f"追问方向提示：{depth_hint or '围绕因果链条继续追问'}。"
                f"可能冲突点：{conflict_setup or '不同立场对风险与机会的权重不同'}。"
                f"不要说'接下来我们来讨论'这种过渡套话。",
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
                    start_line = await guest.generate_line(
                        shared_context,
                        f"你刚要回应关于「{talking_point}」的讨论，但你的发言会被{interrupter_name}打断。"
                        f"所以只说前半句话就被截断了——大概20-40字就被打断，句子可以不完整，"
                        f"用「——」或「…」结尾表示被打断。"
                        f"从你的{guest.persona.occupation}视角出发。",
                    )
                    _append_line(start_line)

                    # Interrupter cuts in
                    interrupt_line = await interrupter.generate_line(
                        shared_context,
                        f"你忍不住打断了{guest_name}的发言！可能因为你太想反驳、太兴奋，"
                        f"或突然想到关键点。请用自然口语切入（如『不好意思打断一下』），"
                        f"然后在40-80字内快速给出核心观点。"
                        f"关于「{talking_point}」，从你的{interrupter.persona.occupation}角度出发。",
                    )
                    _append_line(interrupt_line)

                    # Original speaker responds / continues
                    resume_line = await guest.generate_line(
                        shared_context,
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
                # Build a more contextual instruction based on position
                if sp_idx == 0:
                    instruction = (
                        f"回应主持人关于「{talking_point}」的讨论。"
                        f"从你{guest.persona.occupation}的真实经验出发分享看法——"
                        f"最好能举一个你亲历或者具体了解的案例。"
                        f"你的立场倾向是：{guest.persona.stance_bias or '保持审慎但有判断'}。"
                    )
                else:
                    prev_speaker = speakers_this_round[sp_idx - 1]
                    prev_guest = guest_map[prev_speaker]
                    stance_diff_hint = (
                        "立场差异明显，建议正面交锋"
                        if (guest.persona.stance_bias or "") != (prev_guest.persona.stance_bias or "")
                        else "立场可能接近，建议提供新证据或新角度"
                    )
                    instruction = (
                        f"你听了{prev_speaker}关于「{talking_point}」的观点。"
                        f"你可以接着ta的话往深了聊，也可以提出不同角度甚至反驳。"
                        f"从你{guest.persona.occupation}的视角出发，给出有新增信息量的回应。"
                        f"你的立场倾向是：{guest.persona.stance_bias or '保持审慎但有判断'}。"
                        f"与前一位嘉宾的立场差异：{stance_diff_hint}。"
                    )

                guest_line = await guest.generate_line(shared_context, instruction)
                _append_line(guest_line)

            # Host follow-up / transition
            if tp_idx < len(plan.talking_points) - 1:
                next_talking_point = plan.talking_point_text(tp_idx + 1)
                followup = await self.host.generate_line(
                    shared_context,
                    f"对嘉宾刚才的观点做一个简短、有态度的回应。"
                    f"可以同意并补充、也可以质疑并追问，或点出核心分歧。"
                    f"然后自然过渡到下一个讨论方向「{next_talking_point}」，"
                    f"不要用'接下来'、'让我们转向'这类套话。",
                )
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

        # --- Closing ---
        closing_hint = plan.closing_text()
        closing_line = await self.host.generate_line(
            shared_context,
            f"节目收尾。不要做长篇总结，也不要说'让我们拭目以待'之类的套话。"
            f"分享一个你在这次讨论后的真实感受、困惑或态度变化，"
            f"简短感谢嘉宾，留一个具体开放问题给听众。{closing_hint}",
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
        """Compile background research + RAG context into a block for agents."""
        lines = [
            f"【本期播客话题】{plan.topic}",
            f"【摘要】{plan.summary}",
            "【讨论要点】" + " / ".join(plan.talking_point_texts()),
            "",
            "【深度搜索资料】",
        ]
        for info in detailed_info:
            lines.append(f"--- 搜索: {info.query} ---")
            if info.answer:
                lines.append(info.answer)
            for result in info.results[:3]:
                lines.append(f"  · {result.title}: {result.content[:300]}")
            lines.append("")

        if rag_context:
            lines.append("")
            lines.append("【知识库检索结果（往期节目、专家观点、事实核查、背景资料）】")
            lines.append(rag_context)

        return "\n".join(lines)

    @staticmethod
    def _get_speaking_order(round_idx: int, guest_names: list[str]) -> list[str]:
        """Rotate which guest speaks first each round."""
        n = len(guest_names)
        if n == 0:
            return []
        start = round_idx % n
        return guest_names[start:] + guest_names[:start]
