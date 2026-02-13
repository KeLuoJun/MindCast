"""Podcast orchestrator — LangGraph pipeline for complete episode generation."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.guest import GuestAgent
from backend.agents.host import HostAgent
from backend.agents.personas import GUEST_PERSONAS
from backend.config import settings
from backend.models import DetailedInfo, DialogueLine, Episode, EpisodePlan
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


class PodcastOrchestrator:
    """End-to-end pipeline: news → topic → script → audio, powered by LangGraph."""

    def __init__(
        self,
        llm: LLMService | None = None,
        news: NewsService | None = None,
        tts: TTSService | None = None,
        audio: AudioService | None = None,
    ) -> None:
        self._llm = llm or get_llm_service()
        self._news = news or get_news_service()
        self._tts = tts or get_tts_service()
        self._audio = audio or audio_service

        self.host = HostAgent(self._llm)
        self.guests = [GuestAgent(p, self._llm) for p in GUEST_PERSONAS]
        self._app = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph pipeline once and reuse for every run."""
        graph = StateGraph(OrchestratorState)
        graph.add_node("fetch_news", self._node_fetch_news)
        graph.add_node("select_topic", self._node_select_topic)
        graph.add_node("deep_research", self._node_deep_research)
        graph.add_node("plan_episode", self._node_plan_episode)
        graph.add_node("generate_dialogue", self._node_generate_dialogue)
        graph.add_node("synthesize_tts", self._node_synthesize_tts)
        graph.add_node("stitch_audio", self._node_stitch_audio)
        graph.add_node("save_episode", self._node_save_episode)

        graph.add_edge(START, "fetch_news")
        graph.add_edge("fetch_news", "select_topic")
        graph.add_edge("select_topic", "deep_research")
        graph.add_edge("deep_research", "plan_episode")
        graph.add_edge("plan_episode", "generate_dialogue")
        graph.add_edge("generate_dialogue", "synthesize_tts")
        graph.add_edge("synthesize_tts", "stitch_audio")
        graph.add_edge("stitch_audio", "save_episode")
        graph.add_edge("save_episode", END)
        return graph

    async def generate_episode(self, progress: ProgressCallback = None) -> Episode:
        """Run the complete podcast generation pipeline via LangGraph."""
        episode = Episode(guests=[g.persona.name for g in self.guests])
        output_dir = settings.ensure_output_dir()
        run_log = EpisodeRunLogger(output_dir / "logs" / f"{episode.id}.jsonl")
        episode.generation_log_path = str(run_log.log_path)

        run_log.event(
            "pipeline",
            "episode generation started",
            payload={"episode_id": episode.id, "guests": episode.guests},
        )

        try:
            final_state = await self._app.ainvoke(
                {
                    "episode": episode,
                    "topic": {},
                    "detailed_info": [],
                    "dialogue": [],
                    "audio_segments": [],
                    "progress": progress,
                    "run_logger": run_log,
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
            for g in self.guests:
                g.reset_history()

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
        await self._emit_progress(state, "topic", "主持人正在选题…")
        topic = await self.host.select_topic(episode.news_sources)
        episode.topic = topic.get("topic", "")
        episode.title = episode.topic
        await self._emit_progress(
            state,
            "topic",
            f"选题完成: {episode.topic}",
            payload=topic,
        )
        return {"episode": episode, "topic": topic}

    async def _node_deep_research(self, state: OrchestratorState) -> OrchestratorState:
        topic = state["topic"]
        await self._emit_progress(state, "research", "正在深度搜索…")
        search_queries = topic.get("search_queries", [])[:5]
        detailed_info: list[DetailedInfo] = []

        for i, query in enumerate(search_queries):
            await self._emit_progress(
                state,
                "research",
                f"深度搜索 ({i + 1}/{len(search_queries)}): {query}",
                payload={"query": query, "index": i +
                         1, "total": len(search_queries)},
            )
            info = await self._news.search_detail(query)
            detailed_info.append(info)
            state["run_logger"].event(
                "research",
                "search result captured",
                payload={
                    "query": query,
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

    async def _node_plan_episode(self, state: OrchestratorState) -> OrchestratorState:
        episode = state["episode"]
        topic = state["topic"]
        detailed_info = state.get("detailed_info", [])

        await self._emit_progress(state, "planning", "主持人正在策划节目大纲…")
        guest_names = [g.persona.name for g in self.guests]
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
        await self._emit_progress(state, "tts", "正在合成语音…")

        audio_segments: list[tuple[bytes, float]] = []
        for i, line in enumerate(dialogue):
            await self._emit_progress(
                state,
                "tts",
                f"语音合成 ({i + 1}/{len(dialogue)}): {line.speaker}",
                payload={"speaker": line.speaker,
                         "emotion": line.emotion, "text_len": len(line.text)},
            )
            audio_bytes = await self._tts.synthesize(
                text=line.ssml_text,
                voice_id=line.voice_id,
                emotion=line.emotion,
            )
            audio_segments.append((audio_bytes, line.pause_after))
            state["run_logger"].event(
                "tts",
                "tts segment generated",
                payload={
                    "index": i + 1,
                    "speaker": line.speaker,
                    "bytes": len(audio_bytes),
                    "pause_after": line.pause_after,
                },
            )

        await self._emit_progress(state, "tts", "语音合成全部完成")
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
        """Generate the full dialogue script turn by turn."""
        dialogue: list[DialogueLine] = []
        shared_context: list[dict[str, str]] = []

        bg_info = self._build_background_info(plan, detailed_info)
        shared_context.append({"role": "system", "content": bg_info})

        guest_map = {g.persona.name: g for g in self.guests}
        guest_names = [g.persona.name for g in self.guests]

        opening_line = await self.host.generate_line(
            shared_context,
            f"现在是节目开场。请自然地介绍今天的话题「{plan.topic}」和三位嘉宾：{'、'.join(guest_names)}。"
            f"开场要亲切自然，简要预告讨论内容。{plan.opening}",
        )
        dialogue.append(opening_line)
        shared_context.append(
            {"role": "assistant", "content": f"[{opening_line.speaker}]: {opening_line.text}"})
        state["run_logger"].event(
            "dialogue",
            "line generated",
            payload={"speaker": opening_line.speaker,
                     "text": opening_line.text, "emotion": opening_line.emotion},
        )

        for tp_idx, talking_point in enumerate(plan.talking_points):
            await self._emit_progress(
                state,
                "dialogue",
                f"讨论要点 {tp_idx + 1}/{len(plan.talking_points)}: {talking_point[:30]}…",
                payload={"talking_point": talking_point, "index": tp_idx + 1},
            )

            host_intro = await self.host.generate_line(
                shared_context,
                f"引入下一个讨论要点：「{talking_point}」。可以向某位嘉宾提问或抛出话题让大家讨论。",
            )
            dialogue.append(host_intro)
            shared_context.append(
                {"role": "assistant", "content": f"[{host_intro.speaker}]: {host_intro.text}"})
            state["run_logger"].event(
                "dialogue",
                "line generated",
                payload={"speaker": host_intro.speaker,
                         "text": host_intro.text, "emotion": host_intro.emotion},
            )

            order = self._get_speaking_order(tp_idx, guest_names)
            speakers_this_round = order[:2] if tp_idx < len(
                plan.talking_points) - 1 else order
            for guest_name in speakers_this_round:
                guest = guest_map[guest_name]
                guest_line = await guest.generate_line(
                    shared_context,
                    f"回应主持人关于「{talking_point}」的讨论。"
                    f"从你的{guest.persona.occupation}视角和{guest.persona.mbti}性格出发发表看法。",
                )
                dialogue.append(guest_line)
                shared_context.append(
                    {"role": "assistant", "content": f"[{guest_line.speaker}]: {guest_line.text}"})
                state["run_logger"].event(
                    "dialogue",
                    "line generated",
                    payload={"speaker": guest_line.speaker,
                             "text": guest_line.text, "emotion": guest_line.emotion},
                )

            if tp_idx < len(plan.talking_points) - 1:
                followup = await self.host.generate_line(
                    shared_context,
                    "简短回应嘉宾的观点，做个小结或追问，然后自然地过渡到下一个讨论要点。",
                )
                dialogue.append(followup)
                shared_context.append(
                    {"role": "assistant", "content": f"[{followup.speaker}]: {followup.text}"})
                state["run_logger"].event(
                    "dialogue",
                    "line generated",
                    payload={"speaker": followup.speaker,
                             "text": followup.text, "emotion": followup.emotion},
                )

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

        closing_line = await self.host.generate_line(
            shared_context,
            f"现在进行节目收尾。简要总结今天的重点讨论，感谢嘉宾和听众，预告下期预期。{plan.closing}",
        )
        dialogue.append(closing_line)
        state["run_logger"].event(
            "dialogue",
            "line generated",
            payload={"speaker": closing_line.speaker,
                     "text": closing_line.text, "emotion": closing_line.emotion},
        )

        return dialogue

    @staticmethod
    def _build_background_info(plan: EpisodePlan, detailed_info: list[DetailedInfo]) -> str:
        """Compile background research into a context block for agents."""
        lines = [
            f"【本期播客话题】{plan.topic}",
            f"【摘要】{plan.summary}",
            "【讨论要点】" + " / ".join(plan.talking_points),
            "",
            "【背景资料】",
        ]
        for info in detailed_info:
            lines.append(f"--- 搜索: {info.query} ---")
            if info.answer:
                lines.append(info.answer)
            for result in info.results[:3]:
                lines.append(f"  · {result.title}: {result.content[:300]}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _get_speaking_order(round_idx: int, guest_names: list[str]) -> list[str]:
        """Rotate which guest speaks first each round."""
        n = len(guest_names)
        if n == 0:
            return []
        start = round_idx % n
        return guest_names[start:] + guest_names[:start]
