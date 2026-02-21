"""Run MindCast text-only pipeline (news -> topic -> research -> script).

Developer mode:
- No CLI args required; run directly.
- Detailed, human-readable step-by-step logs.
- Skips TTS/audio stitching completely.
"""

from __future__ import annotations

import asyncio
import logging
import random
import sys
import time
from pathlib import Path

from backend.agents.guest import GuestAgent
from backend.agents.host import HostAgent
from backend.agents.personas import GUEST_PERSONAS
from backend.config import settings
from backend.models import DetailedInfo, DialogueLine, Episode, EpisodePlan
from backend.services.llm_service import get_llm_service
from backend.services.news_service import get_news_service

MAX_NEWS_RESULTS = 10
MAX_SEARCH_QUERIES = 5
PREVIEW_LINES = 8
DEBUG_LOG = True


def _setup_logging() -> None:
    from backend.logging_config import setup_logging
    setup_logging(level=logging.DEBUG if DEBUG_LOG else logging.INFO)


class DevTrace:
    """Human-readable pipeline trace logger for developers."""

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self._step = 0

    def section(self, title: str) -> None:
        self.logger.info("\n%s\n", "=" * 24 + f" {title} " + "=" * 24)

    def start(self, stage: str, detail: str) -> float:
        self._step += 1
        self.logger.info("[STEP %02d][%s] START - %s",
                         self._step, stage, detail)
        return time.perf_counter()

    def done(self, stage: str, detail: str, started_at: float) -> None:
        elapsed = time.perf_counter() - started_at
        self.logger.info("[STEP %02d][%s] DONE  - %s (%.3fs)",
                         self._step, stage, detail, elapsed)

    def detail(self, stage: str, message: str, *, level: str = "debug") -> None:
        log_fn = self.logger.debug if level == "debug" else self.logger.info
        log_fn("[%-8s] %s", stage, message)

    def line(self, index: int, line: DialogueLine) -> None:
        self.logger.info(
            "[LINE %02d] %s | emotion=%s | len=%d",
            index,
            line.speaker,
            line.emotion,
            len(line.text),
        )
        self.logger.debug("[LINE %02d][TEXT] %s", index, line.text)


class TextPipelineRunner:
    """Text-only pipeline runner without TTS/audio dependencies."""

    def __init__(self) -> None:
        self._llm = get_llm_service()
        self._news = get_news_service()
        self.host = HostAgent(self._llm)
        # Select 1-2 guests randomly from the pool
        num_guests = random.randint(1, 2)
        selected_personas = random.sample(GUEST_PERSONAS, num_guests)
        self.guests = [GuestAgent(persona, self._llm)
                       for persona in selected_personas]

    async def generate_dialogue(
        self,
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
        trace: DevTrace,
        rag_context: str = "",
    ) -> list[DialogueLine]:
        dialogue: list[DialogueLine] = []
        shared_context: list[dict[str, str]] = []

        bg_info = self._build_background_info(plan, detailed_info, rag_context)
        shared_context.append({"role": "system", "content": bg_info})
        trace.detail(
            "dialogue", f"shared context initialized, background chars={len(bg_info)}")

        guest_map = {guest.persona.name: guest for guest in self.guests}
        guest_names = [guest.persona.name for guest in self.guests]

        def _append_line(line: DialogueLine) -> None:
            dialogue.append(line)
            shared_context.append(
                {"role": "assistant", "content": f"[{line.speaker}]: {line.text}"})
            trace.line(len(dialogue), line)

        opening_hint = plan.opening_text()
        opening_line = await self.host.generate_line(
            shared_context,
            f"现在是节目开场。请用一种轻松自然的方式带出今天的话题「{plan.topic}」，"
            f"顺便介绍三位嘉宾：{'、'.join(guest_names)}。"
            f"开场要求：别搞『欢迎收听』模板；可用反直觉事实、尖锐问题或生活化场景做钩子；"
            f"可轻微表达你的立场或困惑。{opening_hint}",
        )
        _append_line(opening_line)

        interruption_count = 0
        max_interruptions = 2

        for tp_idx, _ in enumerate(plan.talking_points):
            talking_point = plan.talking_point_text(tp_idx)
            depth_hint = plan.talking_point_depth_hint(tp_idx)
            conflict_setup = plan.talking_point_conflict_setup(tp_idx)
            trace.detail(
                "dialogue",
                f"talking_point {tp_idx + 1}/{len(plan.talking_points)} -> {talking_point}",
                level="info",
            )

            host_intro = await self.host.generate_line(
                shared_context,
                f"引入讨论要点：「{talking_point}」。"
                f"可以向某位嘉宾抛出具体问题，或用意外事实/数据开场，或给一个假设场景让对方判断。"
                f"追问方向提示：{depth_hint or '围绕因果链条继续追问'}。"
                f"可能冲突点：{conflict_setup or '不同立场对风险与机会的权重不同'}。"
                f"不要说'接下来我们来讨论'这种过渡套话。",
            )
            _append_line(host_intro)

            order = self._get_speaking_order(tp_idx, guest_names)
            trace.detail("dialogue", f"speaker order: {order}")
            speakers_this_round = order[:2] if tp_idx < len(
                plan.talking_points) - 1 else order

            for sp_idx, guest_name in enumerate(speakers_this_round):
                guest = guest_map[guest_name]

                # --- Interruption simulation ---
                should_interrupt = (
                    interruption_count < max_interruptions
                    and sp_idx == 0
                    and tp_idx > 0
                    and len(speakers_this_round) > 1
                    and random.random() < 0.35
                )

                if should_interrupt:
                    interrupter_name = speakers_this_round[1]
                    interrupter = guest_map[interrupter_name]

                    trace.detail(
                        "dialogue", f"** INTERRUPTION: {interrupter_name} interrupts {guest_name} **", level="info")

                    start_line = await guest.generate_line(
                        shared_context,
                        f"你刚要回应关于「{talking_point}」的讨论，但你的发言会被{interrupter_name}打断。"
                        f"所以只说前半句话就被截断了——大概20-40字就被打断，句子可以不完整，"
                        f"用「——」或「…」结尾表示被打断。"
                        f"从你的{guest.persona.occupation}视角出发。",
                    )
                    _append_line(start_line)

                    interrupt_line = await interrupter.generate_line(
                        shared_context,
                        f"你忍不住打断了{guest_name}的发言！可能因为你太想反驳、太兴奋，"
                        f"或突然想到关键点。请用自然口语切入（如『不好意思打断一下』），"
                        f"然后在40-80字内快速给出核心观点。"
                        f"关于「{talking_point}」，从你的{interrupter.persona.occupation}角度出发。",
                    )
                    _append_line(interrupt_line)

                    resume_line = await guest.generate_line(
                        shared_context,
                        f"你被{interrupter_name}打断了。现在你可以接着说或者回应ta的观点。"
                        f"可以表现出被打断的反应——笑着说'行行行让你先说完'、"
                        f"'你这么一说我倒想起来了'、或者直接接上'对对对但是我要说的是'。",
                    )
                    _append_line(resume_line)

                    interruption_count += 1
                    continue

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
            trace.detail("dialogue", f"running char count={current_words}")
            if current_words >= settings.target_word_count_max:
                trace.detail(
                    "dialogue",
                    f"target char count reached ({current_words}/{settings.target_word_count_max}), stop early",
                    level="info",
                )
                break

        closing_hint = plan.closing_text()
        closing_line = await self.host.generate_line(
            shared_context,
            f"节目收尾。不要做长篇总结，也不要说'让我们拭目以待'之类的套话。"
            f"分享一个你在这次讨论后的真实感受、困惑或态度变化，"
            f"简短感谢嘉宾，留一个具体开放问题给听众。{closing_hint}",
        )
        _append_line(closing_line)
        return dialogue

    @staticmethod
    def _build_background_info(
        plan: EpisodePlan,
        detailed_info: list[DetailedInfo],
        rag_context: str = "",
    ) -> str:
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
        count = len(guest_names)
        if count == 0:
            return []
        start = round_idx % count
        return guest_names[start:] + guest_names[:start]

    def reset_history(self) -> None:
        self.host.reset_history()
        for guest in self.guests:
            guest.reset_history()


def _attach_file_logger(episode_id: str) -> tuple[logging.Logger, str]:
    logger = logging.getLogger("mindcast.text_pipeline")
    log_path = Path.cwd() / f"{episode_id}.text_only.dev.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if DEBUG_LOG else logging.INFO)
    from backend.logging_config import MindCastFormatter
    file_handler.setFormatter(MindCastFormatter())

    has_same_file = False
    for existing in logger.handlers:
        if isinstance(existing, logging.FileHandler) and getattr(existing, "baseFilename", "") == str(log_path):
            has_same_file = True
            break
    if not has_same_file:
        logger.addHandler(file_handler)

    return logger, str(log_path)


async def run_text_pipeline(topic: str = "") -> Episode:
    user_topic = topic.strip()
    runner = TextPipelineRunner()

    episode = Episode(guests=[g.persona.name for g in runner.guests])
    logger, log_path = _attach_file_logger(episode.id)
    trace = DevTrace(logger)
    trace.section("TEXT-ONLY PIPELINE")
    trace.detail("pipeline", f"episode_id={episode.id}", level="info")
    trace.detail("pipeline", f"guests={episode.guests}", level="info")
    episode.generation_log_path = log_path

    output_dir = settings.ensure_output_dir()

    try:
        started = trace.start(
            "news", f"fetching news (max_results={MAX_NEWS_RESULTS})")
        news_items = await runner._news.get_topic_news(topic=user_topic, max_results=MAX_NEWS_RESULTS)
        if not news_items:
            raise RuntimeError("No news items retrieved from Tavily")
        episode.news_sources = news_items
        trace.done("news", f"fetched {len(news_items)} news items", started)
        for idx, item in enumerate(news_items, start=1):
            trace.detail(
                "news",
                f"#{idx} {item.title} | date={item.published_date or '-'} | score={item.score}",
            )

        started = trace.start("topic", "host selecting topic")
        topic = await runner.host.select_topic(news_items)
        episode.topic = topic.get("topic", "")
        episode.title = episode.topic
        trace.done("topic", f"selected: {episode.topic}", started)
        trace.detail("topic", f"reason={topic.get('reason', '')}")

        started = trace.start("research", "running deep research")
        raw_queries = topic.get("search_queries", [])
        search_queries = raw_queries[:MAX_SEARCH_QUERIES]
        trace.detail("research", f"queries={search_queries}", level="info")
        detailed_info: list[DetailedInfo] = []
        for index, query in enumerate(search_queries, start=1):
            query_started = time.perf_counter()
            trace.detail(
                "research", f"[{index}/{len(search_queries)}] query={query}", level="info")
            info = await runner._news.search_detail(query)
            detailed_info.append(info)
            elapsed = time.perf_counter() - query_started
            trace.detail(
                "research",
                f"[{index}/{len(search_queries)}] answer_len={len(info.answer or '')} results={len(info.results)} ({elapsed:.3f}s)",
            )
            for r_idx, result in enumerate(info.results[:3], start=1):
                trace.detail("research", f"  top{r_idx}: {result.title}")
        trace.done(
            "research", f"completed {len(detailed_info)} query groups", started)

        # RAG knowledge base retrieval
        rag_context = ""
        try:
            from backend.knowledge import get_knowledge_base
            started = trace.start("rag", "retrieving from knowledge base")
            kb = get_knowledge_base()
            rag_context = await kb.build_rag_context(
                episode.topic, top_k_per_collection=3,
            )
            stats = kb.get_collection_stats()
            trace.done(
                "rag", f"rag_context_len={len(rag_context)}, stats={stats}", started)
        except Exception as exc:
            trace.detail(
                "rag", f"KB retrieval failed (non-fatal): {exc}", level="info")

        started = trace.start("planning", "host creating episode plan")
        plan = await runner.host.plan_episode(
            topic,
            [info.model_dump() for info in detailed_info],
            [guest.persona.name for guest in runner.guests],
        )
        episode.summary = plan.summary
        trace.done(
            "planning", f"talking_points={len(plan.talking_points)}", started)
        trace.detail("planning", f"summary={plan.summary}")
        for index, talking_point in enumerate(plan.talking_points, start=1):
            trace.detail(
                "planning", f"point {index}: {plan.talking_point_text(index - 1)}")

        started = trace.start("dialogue", "generating dialogue script")
        dialogue = await runner.generate_dialogue(
            plan,
            detailed_info,
            trace,
            rag_context=rag_context,
        )
        episode.dialogue = dialogue
        episode.word_count = sum(len(line.text) for line in dialogue)
        trace.done(
            "dialogue",
            f"generated {len(dialogue)} lines, total chars={episode.word_count}",
            started,
        )

        metadata_path = episode.save_json(output_dir)

        # Ingest episode into knowledge base
        try:
            from backend.knowledge import get_knowledge_base
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
            trace.detail(
                "kb", f"episode {episode.id} ingested into knowledge base", level="info")
        except Exception as exc:
            trace.detail(
                "kb", f"KB ingestion failed (non-fatal): {exc}", level="info")

        trace.section("PIPELINE RESULT")
        trace.detail("result", f"episode_json={metadata_path}", level="info")
        trace.detail("result", f"developer_log={log_path}", level="info")
        trace.detail(
            "result", f"previewing first {min(PREVIEW_LINES, len(dialogue))} lines", level="info")

        for line in dialogue[:PREVIEW_LINES]:
            logger.info("[PREVIEW] %s: %s", line.speaker, line.text)

        return episode
    except Exception:
        logger.exception("Text-only pipeline failed")
        raise
    finally:
        runner.reset_history()


def main() -> None:
    _setup_logging()
    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    asyncio.run(run_text_pipeline(topic=topic))


if __name__ == "__main__":
    main()
