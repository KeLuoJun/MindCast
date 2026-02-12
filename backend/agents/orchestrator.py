"""Podcast orchestrator — the core pipeline that generates a complete episode."""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Callable, Awaitable
from typing import Any

from backend.agents.guest import GuestAgent
from backend.agents.host import HostAgent
from backend.agents.personas import GUEST_PERSONAS, HOST_PERSONA, build_system_prompt
from backend.config import settings
from backend.models import DetailedInfo, DialogueLine, Episode, EpisodePlan, NewsItem
from backend.services.llm_service import LLMService, get_llm_service
from backend.services.news_service import NewsService, get_news_service
from backend.services.tts_service import TTSService, get_tts_service
from backend.services.audio_service import AudioService, audio_service

logger = logging.getLogger(__name__)

# Type alias for progress callbacks
ProgressCallback = Callable[[str, str], Awaitable[None]] | None


class PodcastOrchestrator:
    """End-to-end pipeline: news → topic → script → audio."""

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

        # Create agents
        self.host = HostAgent(self._llm)
        self.guests = [GuestAgent(p, self._llm) for p in GUEST_PERSONAS]

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    async def generate_episode(
        self,
        progress: ProgressCallback = None,
    ) -> Episode:
        """Run the complete podcast generation pipeline."""
        episode = Episode(guests=[g.persona.name for g in self.guests])

        async def _report(stage: str, detail: str = "") -> None:
            logger.info("[%s] %s", stage, detail)
            if progress:
                await progress(stage, detail)

        # 1. Fetch daily AI news
        await _report("news", "正在获取AI资讯…")
        news_items = await self._news.get_daily_ai_news(max_results=10)
        if not news_items:
            raise RuntimeError("No news items retrieved from Tavily")
        episode.news_sources = news_items
        await _report("news", f"获取到{len(news_items)}条资讯")

        # 2. Host selects topic
        await _report("topic", "主持人正在选题…")
        topic = await self.host.select_topic(news_items)
        episode.topic = topic.get("topic", "")
        episode.title = episode.topic
        await _report("topic", f"选题完成: {episode.topic}")

        # 3. Deep search (up to 5 queries)
        await _report("research", "正在深度搜索…")
        search_queries = topic.get("search_queries", [])[:5]
        detailed_info: list[DetailedInfo] = []
        for i, q in enumerate(search_queries):
            await _report("research", f"深度搜索 ({i+1}/{len(search_queries)}): {q}")
            info = await self._news.search_detail(q)
            detailed_info.append(info)
        await _report("research", f"完成{len(detailed_info)}轮深度搜索")

        # 4. Host plans episode
        await _report("planning", "主持人正在策划节目大纲…")
        guest_names = [g.persona.name for g in self.guests]
        plan = await self.host.plan_episode(
            topic,
            [info.model_dump() for info in detailed_info],
            guest_names,
        )
        episode.summary = plan.summary
        await _report("planning", f"大纲完成: {len(plan.talking_points)}个讨论要点")

        # 5. Generate dialogue
        await _report("dialogue", "正在生成播客对话…")
        dialogue = await self._generate_dialogue(plan, detailed_info, _report)
        episode.dialogue = dialogue
        episode.word_count = sum(len(line.text) for line in dialogue)
        await _report("dialogue", f"对话生成完成: {len(dialogue)}条台词, {episode.word_count}字")

        # 6. TTS synthesis
        await _report("tts", "正在合成语音…")
        audio_segments: list[tuple[bytes, float]] = []
        for i, line in enumerate(dialogue):
            await _report("tts", f"语音合成 ({i+1}/{len(dialogue)}): {line.speaker}")
            audio_bytes = await self._tts.synthesize(
                text=line.ssml_text,
                voice_id=line.voice_id,
                emotion=line.emotion,
            )
            audio_segments.append((audio_bytes, line.pause_after))
        await _report("tts", "语音合成全部完成")

        # 7. Stitch audio
        await _report("audio", "正在拼接音频…")
        output_dir = settings.ensure_output_dir()
        output_path = output_dir / f"{episode.id}.mp3"
        duration = await self._audio.stitch_episode(
            audio_segments=audio_segments,
            output_path=str(output_path),
        )
        episode.audio_path = str(output_path)
        episode.duration_seconds = duration
        await _report("audio", f"音频拼接完成: {duration:.1f}秒")

        # 8. Save metadata
        episode.save_json(output_dir)
        await _report("done", f"播客生成完成！ID: {episode.id}")

        # Reset agent histories for next episode
        self.host.reset_history()
        for g in self.guests:
            g.reset_history()

        return episode

    # ------------------------------------------------------------------
    # Dialogue generation (turn-by-turn)
    # ------------------------------------------------------------------

    async def _generate_dialogue(
        self,
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
        report: Callable,
    ) -> list[DialogueLine]:
        """Generate the full dialogue script turn by turn."""
        dialogue: list[DialogueLine] = []
        shared_context: list[dict[str, str]] = []

        # Inject background knowledge into shared context
        bg_info = self._build_background_info(plan, detailed_info)
        shared_context.append({
            "role": "system",
            "content": bg_info,
        })

        guest_map = {g.persona.name: g for g in self.guests}
        guest_names = [g.persona.name for g in self.guests]

        # --- Opening ---
        opening_line = await self.host.generate_line(
            shared_context,
            f"现在是节目开场。请自然地介绍今天的话题「{plan.topic}」和三位嘉宾：{'、'.join(guest_names)}。"
            f"开场要亲切自然，简要预告讨论内容。{plan.opening}",
        )
        dialogue.append(opening_line)
        shared_context.append({
            "role": "assistant",
            "content": f"[{opening_line.speaker}]: {opening_line.text}",
        })

        # --- Discussion rounds (one per talking point) ---
        for tp_idx, talking_point in enumerate(plan.talking_points):
            await report("dialogue", f"讨论要点 {tp_idx+1}/{len(plan.talking_points)}: {talking_point[:30]}…")

            # Host introduces the talking point
            host_intro = await self.host.generate_line(
                shared_context,
                f"引入下一个讨论要点：「{talking_point}」。"
                f"可以向某位嘉宾提问或抛出话题让大家讨论。",
            )
            dialogue.append(host_intro)
            shared_context.append({
                "role": "assistant",
                "content": f"[{host_intro.speaker}]: {host_intro.text}",
            })

            # Determine speaking order for this round (rotate lead guest)
            order = self._get_speaking_order(tp_idx, guest_names)

            # Each guest responds (typically 2 guests per point + host follow-up)
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
                shared_context.append({
                    "role": "assistant",
                    "content": f"[{guest_line.speaker}]: {guest_line.text}",
                })

            # Host follow-up / transition (except after last point)
            if tp_idx < len(plan.talking_points) - 1:
                followup = await self.host.generate_line(
                    shared_context,
                    "简短回应嘉宾的观点，做个小结或追问，然后自然地过渡到下一个讨论要点。",
                )
                dialogue.append(followup)
                shared_context.append({
                    "role": "assistant",
                    "content": f"[{followup.speaker}]: {followup.text}",
                })

            # Word count check — stop early if near target
            current_words = sum(len(line.text) for line in dialogue)
            if current_words >= settings.target_word_count_max:
                logger.info(
                    "Reached target word count (%d), wrapping up.", current_words)
                break

        # --- Closing ---
        closing_line = await self.host.generate_line(
            shared_context,
            f"现在进行节目收尾。简要总结今天的重点讨论，感谢嘉宾和听众，预告下期预期。{plan.closing}",
        )
        dialogue.append(closing_line)

        return dialogue

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_background_info(
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
    ) -> str:
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
            for r in info.results[:3]:
                lines.append(f"  · {r.title}: {r.content[:300]}")
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
