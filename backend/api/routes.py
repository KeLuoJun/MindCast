"""FastAPI route definitions."""

from __future__ import annotations

import asyncio
import json
import logging
import random
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.agents.orchestrator import PodcastOrchestrator
from backend.api.schemas import (
    AppSettingsOut,
    AppSettingsPatch,
    DialogueLineOut,
    EpisodeDetail,
    EpisodeAudioRetimeRequest,
    EpisodeSummary,
    GuestGenerateRequest,
    GuestProfileIn,
    GuestProfileOut,
    GenerateRequest,
    ScriptSynthesisRequest,
    ScriptPreviewRequest,
    TaskCreatedResponse,
    VoiceLibraryResponse,
)
from backend.config import settings
from backend.knowledge import get_knowledge_base
from backend.knowledge.chroma_kb import (
    BACKGROUND_MATERIAL,
    KNOWLEDGE_SCOPE_GLOBAL,
)
from backend.models import DetailedInfo, DialogueLine, Episode
from backend.services.run_logger import EpisodeRunLogger
from backend.services.news_service import get_news_service
from backend.services.guest_pool_service import get_guest_pool_service, to_persona_config
from backend.services.host_service import get_host_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory task tracking (MVP — no persistent task store)
_tasks: dict[str, dict] = {}
_task_jobs: dict[str, asyncio.Task] = {}


# ---------------------------------------------------------------------------
# Debug endpoints — stage-by-stage backend verification
# ---------------------------------------------------------------------------

async def _translate_to_chinese(text: str, llm_service) -> str:
    """Translate English text to Chinese using LLM."""
    if not text or not text.strip():
        return text
    # Check if text contains English letters (simple detection)
    has_english = any('\u0041' <= c <= '\u005a' or '\u0061' <=
                      c <= '\u007a' for c in text)
    if not has_english:
        return text  # Already Chinese or no English

    try:
        messages = [
            {"role": "system", "content": "You are a translator. Translate the following news title and content to Chinese. Keep the translation natural and concise. Only return the translated text, no explanations."},
            {"role": "user", "content": text}
        ]
        translated = await llm_service.chat(messages, temperature=0.3, max_tokens=1024)
        return translated.strip() if translated else text
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text


@router.get("/debug/news")
async def debug_news(max_results: int = 6, topic: str = ""):
    """Fetch news by topic (without topic/script/audio generation)."""
    from backend.services.llm_service import get_llm_service

    service = get_news_service()
    items = await service.get_topic_news(topic=topic, max_results=max_results)

    # Translate to Chinese if needed
    llm = get_llm_service()
    translated_items = []
    for item in items:
        translated_title = await _translate_to_chinese(item.title, llm)
        translated_content = await _translate_to_chinese(item.content, llm) if item.content else item.content
        item.title = translated_title
        item.content = translated_content
        translated_items.append(item)

    return {
        "count": len(translated_items),
        "items": [item.model_dump() for item in translated_items],
    }


@router.post("/debug/script")
async def debug_script_preview(req: ScriptPreviewRequest | None = None):
    """Run pipeline until dialogue generation (skip TTS and audio stitching)."""
    payload = req or ScriptPreviewRequest()
    guest_pool_service = get_guest_pool_service()
    guest_pool = guest_pool_service.list_guests()
    orchestrator = PodcastOrchestrator(guest_personas=guest_pool)

    selected_names = [name.strip()
                      for name in payload.selected_guests if name and name.strip()]
    if selected_names:
        unknown = [
            name for name in selected_names if name not in orchestrator._guest_pool]
        if unknown:
            raise HTTPException(
                status_code=400, detail=f"Unknown guests: {', '.join(unknown)}")
        if len(selected_names) > settings.max_guests:
            raise HTTPException(
                status_code=400, detail=f"最多可选择{settings.max_guests}位嘉宾")
    else:
        num_guests = random.randint(1, 2)
        selected_names = random.sample(
            list(orchestrator._guest_pool.keys()), num_guests)

    active_guests = [orchestrator._guest_pool[name] for name in selected_names]
    speaker_voice_map = orchestrator._build_speaker_voice_map(active_guests)

    news_items = await orchestrator._news.get_topic_news(
        topic=payload.topic, max_results=payload.max_news_results
    )
    if not news_items:
        raise HTTPException(status_code=502, detail="No news items retrieved")

    if payload.topic.strip():
        selected_topic = payload.topic.strip()
        topic = {
            "topic": selected_topic,
            "reason": "用户手动选择话题",
            "search_queries": [
                selected_topic,
                f"{selected_topic} 最新进展",
                f"{selected_topic} 行业争议",
            ],
        }
    else:
        recent_topics = orchestrator._load_recent_topics(
            limit=20,
        )
        topic = await orchestrator.host.select_topic(
            news_items,
            recent_topics=recent_topics,
        )
    search_queries = topic.get("search_queries", [])[
        : payload.max_search_queries]

    detailed_info: list[DetailedInfo] = []
    kb = get_knowledge_base()
    for query in search_queries:
        rag_docs = await kb.query(
            query,
            top_k=4,
            collection=BACKGROUND_MATERIAL,
            scope=KNOWLEDGE_SCOPE_GLOBAL,
        )
        rag_snippets = [d.get("content", "")
                        for d in rag_docs if d.get("content")]
        decision = await orchestrator.host.decide_need_fresh_search(query, rag_snippets)
        need_fresh_search = bool(decision.get("need_fresh_search", False))
        if not rag_snippets:
            need_fresh_search = True

        if need_fresh_search:
            focus_query = decision.get("focus", "").strip() or query
            detailed_info.append(await orchestrator._news.search_detail(focus_query))
        else:
            rag_answer = "\n\n".join(
                f"- {txt[:300]}" for txt in rag_snippets[:4])
            detailed_info.append(
                DetailedInfo(
                    query=query,
                    answer=f"基于知识库历史资料整理：\n{rag_answer}" if rag_answer else "",
                    results=[],
                )
            )

    plan = await orchestrator.host.plan_episode(
        topic,
        [info.model_dump() for info in detailed_info],
        selected_names,
    )

    episode = Episode(
        topic=plan.topic,
        title=plan.topic,
        summary=plan.summary,
        guests=selected_names,
    )
    # Retrieve RAG context
    rag_context = ""
    try:
        kb = get_knowledge_base()
        rag_context = await kb.build_rag_context(plan.topic, top_k_per_collection=3)
    except Exception:
        logger.warning(
            "RAG retrieval failed in debug endpoint, continuing without")

    output_dir = settings.ensure_output_dir()
    run_logger = EpisodeRunLogger(
        output_dir / "logs" / f"{episode.id}.debug.jsonl")
    dialogue = await orchestrator._generate_dialogue(
        plan,
        detailed_info,
        {
            "episode": episode,
            "progress": None,
            "run_logger": run_logger,
            "rag_context": rag_context,
            "active_guests": active_guests,
            "speaker_voice_map": speaker_voice_map,
        },
    )
    word_count = sum(len(line.text) for line in dialogue)

    orchestrator.host.reset_history()
    for guest in active_guests:
        guest.reset_history()

    return {
        "title": plan.topic,
        "topic": plan.topic,
        "summary": plan.summary,
        "guests": selected_names,
        "talking_points": plan.talking_point_texts(),
        "word_count": word_count,
        "line_count": len(dialogue),
        "news_count": len(news_items),
        "search_queries": search_queries,
        "generation_log_path": str(run_logger.log_path),
        "news_sources": [item.model_dump() for item in news_items],
        "dialogue": [
            {
                "speaker": line.speaker,
                "text": line.text,
                "emotion": line.emotion,
            }
            for line in dialogue
        ],
    }


@router.post("/script/preview")
async def script_preview(req: ScriptPreviewRequest | None = None):
    """Preview generated script for manual confirmation/editing."""
    return await debug_script_preview(req)


@router.post("/script/preview/task", response_model=TaskCreatedResponse)
async def script_preview_task(req: ScriptPreviewRequest | None = None):
    """Start script preview generation as a background task with SSE progress."""
    payload = req or ScriptPreviewRequest()

    task_id = f"task_{len(_tasks) + 1}"
    _tasks[task_id] = {
        "status": "started",
        "stage": "news",
        "detail": "正在获取资讯...",
        "episode_id": None,
        "result": None,
    }

    async def _run():
        guest_pool_service = get_guest_pool_service()
        guest_pool = guest_pool_service.list_guests()
        orchestrator = PodcastOrchestrator(guest_personas=guest_pool)

        selected_names = [n.strip()
                          for n in payload.selected_guests if n and n.strip()]
        if selected_names:
            unknown = [
                n for n in selected_names if n not in orchestrator._guest_pool]
            if unknown:
                _tasks[task_id].update({
                    "status": "failed", "stage": "error",
                    "detail": f"Unknown guests: {', '.join(unknown)}"
                })
                return
            if len(selected_names) > settings.max_guests:
                _tasks[task_id].update({
                    "status": "failed", "stage": "error",
                    "detail": f"最多可选择{settings.max_guests}位嘉宾"
                })
                return
        else:
            num_guests = random.randint(1, 2)
            selected_names = random.sample(
                list(orchestrator._guest_pool.keys()), num_guests)

        active_guests = [orchestrator._guest_pool[name]
                         for name in selected_names]
        speaker_voice_map = orchestrator._build_speaker_voice_map(
            active_guests)

        try:
            _tasks[task_id].update({"stage": "news", "detail": "正在获取资讯..."})
            news_items = await orchestrator._news.get_topic_news(
                topic=payload.topic, max_results=payload.max_news_results
            )
            if not news_items:
                raise RuntimeError("未获取到相关资讯")

            _tasks[task_id].update({"stage": "topic", "detail": "正在分析选定话题..."})
            if payload.topic.strip():
                selected_topic = payload.topic.strip()
                topic = {
                    "topic": selected_topic,
                    "reason": "用户手动选择话题",
                    "search_queries": [
                        selected_topic,
                        f"{selected_topic} 最新进展",
                        f"{selected_topic} 行业争议",
                    ],
                }
            else:
                recent_topics = orchestrator._load_recent_topics(limit=20)
                topic = await orchestrator.host.select_topic(news_items, recent_topics=recent_topics)
            search_queries = topic.get("search_queries", [])[
                :payload.max_search_queries]

            _tasks[task_id].update({
                "stage": "research",
                "detail": f"深度研究中：{topic.get('topic', '')}...",
            })
            detailed_info: list[DetailedInfo] = []
            kb = get_knowledge_base()
            for query in search_queries:
                rag_docs = await kb.query(
                    query, top_k=4, collection=BACKGROUND_MATERIAL, scope=KNOWLEDGE_SCOPE_GLOBAL
                )
                rag_snippets = [d.get("content", "")
                                for d in rag_docs if d.get("content")]
                decision = await orchestrator.host.decide_need_fresh_search(query, rag_snippets)
                need_fresh_search = bool(
                    decision.get("need_fresh_search", False))
                if not rag_snippets:
                    need_fresh_search = True
                if need_fresh_search:
                    focus_query = decision.get("focus", "").strip() or query
                    detailed_info.append(await orchestrator._news.search_detail(focus_query))
                else:
                    rag_answer = "\n\n".join(
                        f"- {txt[:300]}" for txt in rag_snippets[:4])
                    detailed_info.append(DetailedInfo(
                        query=query,
                        answer=f"基于知识库历史资料整理：\n{rag_answer}" if rag_answer else "",
                        results=[],
                    ))

            _tasks[task_id].update(
                {"stage": "planning", "detail": "正在策划节目结构..."})
            plan = await orchestrator.host.plan_episode(
                topic, [info.model_dump()
                        for info in detailed_info], selected_names
            )

            episode = Episode(topic=plan.topic, title=plan.topic,
                              summary=plan.summary, guests=selected_names)
            rag_context = ""
            try:
                rag_context = await kb.build_rag_context(plan.topic, top_k_per_collection=3)
            except Exception:
                logger.warning(
                    "RAG retrieval failed in preview task, continuing without")

            output_dir = settings.ensure_output_dir()
            run_logger = EpisodeRunLogger(
                output_dir / "logs" / f"{episode.id}.debug.jsonl")

            _tasks[task_id].update(
                {"stage": "dialogue", "detail": "正在生成对话内容..."})
            dialogue = await orchestrator._generate_dialogue(
                plan,
                detailed_info,
                {
                    "episode": episode,
                    "progress": None,
                    "run_logger": run_logger,
                    "rag_context": rag_context,
                    "active_guests": active_guests,
                    "speaker_voice_map": speaker_voice_map,
                },
            )

            orchestrator.host.reset_history()
            for guest in active_guests:
                guest.reset_history()

            _tasks[task_id].update({
                "status": "completed",
                "stage": "done",
                "detail": "文稿生成完成",
                "result": {
                    "title": plan.topic,
                    "topic": plan.topic,
                    "summary": plan.summary,
                    "guests": selected_names,
                    "dialogue": [
                        {"speaker": line.speaker, "text": line.text,
                            "emotion": line.emotion}
                        for line in dialogue
                    ],
                },
            })
        except asyncio.CancelledError:
            _tasks[task_id].update({
                "status": "cancelled",
                "stage": "cancelled",
                "detail": "任务已终止",
            })
            raise
        except Exception as exc:
            logger.exception("Script preview task failed")
            _tasks[task_id].update(
                {"status": "failed", "stage": "error", "detail": str(exc)})
        finally:
            _task_jobs.pop(task_id, None)

    _task_jobs[task_id] = asyncio.create_task(_run())
    return TaskCreatedResponse(task_id=task_id, message="文稿预览任务已创建")


@router.post("/script/synthesize", response_model=TaskCreatedResponse)
async def synthesize_from_script(req: ScriptSynthesisRequest):
    """Synthesize audio from frontend-edited script in background."""
    if not req.dialogue:
        raise HTTPException(status_code=400, detail="Dialogue is required")

    task_id = f"task_{len(_tasks) + 1}"
    _tasks[task_id] = {
        "status": "started",
        "stage": "audio",
        "detail": "正在准备语音合成…",
        "episode_id": None,
    }

    async def _run():
        orchestrator = PodcastOrchestrator()

        async def _progress(stage: str, detail: str):
            _tasks[task_id].update({"stage": stage, "detail": detail})

        try:
            dialogue_lines = [
                {
                    "speaker": line.speaker,
                    "text": line.text,
                    "ssml_text": line.text,
                    "emotion": line.emotion or "neutral",
                    "voice_id": line.voice_id or "",
                    "speech_rate": line.speech_rate,
                }
                for line in req.dialogue
                if line.text.strip()
            ]
            if not dialogue_lines:
                raise RuntimeError("Dialogue is empty after filtering")

            episode = await orchestrator.synthesize_episode_from_script(
                title=req.title,
                topic=req.topic,
                summary=req.summary,
                guests=req.guests,
                dialogue=[
                    DialogueLine(**line)
                    for line in dialogue_lines
                ],
                news_sources=req.news_sources,
                progress=_progress,
            )
            _tasks[task_id].update({
                "status": "completed",
                "stage": "done",
                "detail": f"完成！ID: {episode.id}",
                "episode_id": episode.id,
            })
        except asyncio.CancelledError:
            _tasks[task_id].update({
                "status": "cancelled",
                "stage": "cancelled",
                "detail": "任务已终止",
            })
            raise
        except Exception as exc:
            logger.exception("Script synthesis failed")
            _tasks[task_id].update({
                "status": "failed",
                "stage": "error",
                "detail": str(exc),
            })
        finally:
            _task_jobs.pop(task_id, None)

    _task_jobs[task_id] = asyncio.create_task(_run())
    return TaskCreatedResponse(task_id=task_id, message="语音合成任务已创建")


@router.post("/episodes/{episode_id}/audio/retime", response_model=TaskCreatedResponse)
async def retime_episode_audio(episode_id: str, req: EpisodeAudioRetimeRequest):
    """Apply per-dialogue speech rates and rebuild episode audio in background."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    task_id = f"task_{len(_tasks) + 1}"
    _tasks[task_id] = {
        "status": "started",
        "stage": "audio",
        "detail": "正在准备段级倍速处理…",
        "episode_id": episode_id,
    }

    async def _run():
        orchestrator = PodcastOrchestrator()

        async def _progress(stage: str, detail: str):
            _tasks[task_id].update({"stage": stage, "detail": detail})

        try:
            episode = Episode.load_json(json_path)
            await orchestrator.retime_episode_audio(
                episode,
                line_speeds=req.line_speeds,
                progress=_progress,
            )
            _tasks[task_id].update({
                "status": "completed",
                "stage": "done",
                "detail": f"段级倍速处理完成！ID: {episode.id}",
                "episode_id": episode.id,
            })
        except asyncio.CancelledError:
            _tasks[task_id].update({
                "status": "cancelled",
                "stage": "cancelled",
                "detail": "任务已终止",
            })
            raise
        except Exception as exc:
            logger.exception("Episode audio retime failed")
            _tasks[task_id].update({
                "status": "failed",
                "stage": "error",
                "detail": str(exc),
            })
        finally:
            _task_jobs.pop(task_id, None)

    _task_jobs[task_id] = asyncio.create_task(_run())
    return TaskCreatedResponse(task_id=task_id, message="段级倍速处理任务已创建")


# ---------------------------------------------------------------------------
# POST /api/generate — trigger new episode
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=TaskCreatedResponse)
async def generate_episode(req: GenerateRequest | None = None):
    """Start generating a new podcast episode in the background."""
    payload = req or GenerateRequest()

    if len(payload.selected_guests) > settings.max_guests:
        raise HTTPException(
            status_code=400, detail=f"最多可选择{settings.max_guests}位嘉宾")

    guest_pool_service = get_guest_pool_service()
    guest_pool = guest_pool_service.list_guests()
    guest_names = {guest.name for guest in guest_pool}
    unknown = [name for name in payload.selected_guests if name not in guest_names]
    if unknown:
        raise HTTPException(
            status_code=400, detail=f"Unknown guests: {', '.join(unknown)}")

    task_id = f"task_{len(_tasks) + 1}"
    _tasks[task_id] = {"status": "started",
                       "stage": "initializing", "detail": "", "episode_id": None}

    async def _run():
        orchestrator = PodcastOrchestrator(guest_personas=guest_pool)

        async def _progress(stage: str, detail: str):
            _tasks[task_id].update({"stage": stage, "detail": detail})

        try:
            episode = await orchestrator.generate_episode(
                progress=_progress,
                topic=payload.topic,
                selected_guest_names=payload.selected_guests,
            )
            _tasks[task_id].update({
                "status": "completed",
                "stage": "done",
                "detail": f"完成！ID: {episode.id}",
                "episode_id": episode.id,
            })
        except asyncio.CancelledError:
            _tasks[task_id].update({
                "status": "cancelled",
                "stage": "cancelled",
                "detail": "任务已终止",
            })
            raise
        except Exception as exc:
            logger.exception("Episode generation failed")
            _tasks[task_id].update({
                "status": "failed",
                "stage": "error",
                "detail": str(exc),
            })
        finally:
            _task_jobs.pop(task_id, None)

    _task_jobs[task_id] = asyncio.create_task(_run())
    return TaskCreatedResponse(task_id=task_id)


# ---------------------------------------------------------------------------
# Guest pool management endpoints
# ---------------------------------------------------------------------------

@router.get("/guests", response_model=list[GuestProfileOut])
async def list_guest_pool():
    service = get_guest_pool_service()
    guests = service.list_guests()
    return [GuestProfileOut(**guest.model_dump(mode="json")) for guest in guests]


@router.post("/guests", response_model=list[GuestProfileOut])
async def create_guest(guest: GuestProfileIn):
    service = get_guest_pool_service()
    try:
        guests = service.add_guest(to_persona_config(guest.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [GuestProfileOut(**item.model_dump(mode="json")) for item in guests]


@router.put("/guests/{guest_name}", response_model=list[GuestProfileOut])
async def update_guest(guest_name: str, guest: GuestProfileIn):
    service = get_guest_pool_service()
    try:
        guests = service.update_guest(
            guest_name, to_persona_config(guest.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [GuestProfileOut(**item.model_dump(mode="json")) for item in guests]


@router.delete("/guests/{guest_name}", response_model=list[GuestProfileOut])
async def delete_guest(guest_name: str):
    service = get_guest_pool_service()
    try:
        guests = service.delete_guest(guest_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [GuestProfileOut(**item.model_dump(mode="json")) for item in guests]


# ---------------------------------------------------------------------------
# Host Persona Management
# ---------------------------------------------------------------------------

@router.get("/host", response_model=GuestProfileOut)
async def get_host_profile():
    """Get the persistent host persona."""
    service = get_host_service()
    host = service.get_host()
    return GuestProfileOut(**host.model_dump(mode="json"))


@router.put("/host", response_model=GuestProfileOut)
async def update_host_profile(payload: GuestProfileIn):
    """Update the host persona."""
    service = get_host_service()
    updated = to_persona_config(payload.model_dump())
    host = service.save_host(updated)
    return GuestProfileOut(**host.model_dump(mode="json"))


# ---------------------------------------------------------------------------
# POST /api/guests/generate — AI-generate guest profile from NL description
# ---------------------------------------------------------------------------

@router.post("/guests/generate", response_model=GuestProfileOut)
async def generate_guest(req: GuestGenerateRequest):
    """Use LLM to generate a full guest profile from a natural-language description."""
    from backend.services.llm_service import get_llm_service
    from backend.agents.personas import VOICE_LIBRARY_BY_GENDER
    from backend.models import Gender

    llm = get_llm_service()
    male_voices = VOICE_LIBRARY_BY_GENDER[Gender.MALE]
    female_voices = VOICE_LIBRARY_BY_GENDER[Gender.FEMALE]

    prompt = f"""根据以下用户描述，为播客节目 MindCast 设计一位嘉宾角色。

用户描述：{req.description}

可选男性音色ID列表：{male_voices}
可选女性音色ID列表：{female_voices}

请从音色列表中选择一个最匹配嘉宾气质的音色ID。
只返回如下JSON，不加任何说明或markdown代码块标记：
{{
  "name": "嘉宾姓名（中文，2-3字，有个性）",
  "gender": "male 或 female",
  "age": 年龄（18-60之间的整数）,
  "mbti": "MBTI类型（如INTJ、ENTP等16种之一）",
  "occupation": "具体职业描述（10字以内）",
  "personality": "性格特征（2-3句，突出独特之处，避免套话）",
  "speaking_style": "说话风格（2-3句，具体描述语言习惯和表达方式）",
  "stance_bias": "观点倾向或认知偏见（1-2句，可为空字符串）",
  "voice_id": "从音色列表中选取最匹配的一个ID",
  "background": "专业背景和经历（2-3句，具体真实）"
}}"""

    messages = [
        {"role": "system", "content": "你是一个播客角色设计师，擅长创建有独特个性的播客嘉宾人物。只返回JSON，不加任何说明文字或markdown标记。"},
        {"role": "user", "content": prompt},
    ]

    try:
        raw = await llm.chat(messages, temperature=0.9, max_tokens=1024)
        raw = raw.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        data = json.loads(raw)
    except Exception as exc:
        logger.error("Guest generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"AI生成失败：{exc}") from exc

    # Sanitize values
    gender = str(data.get("gender", "male")).strip().lower()
    if gender not in ("male", "female"):
        gender = "male"
    data["gender"] = gender
    try:
        age = max(18, min(60, int(data.get("age", 30))))
    except (TypeError, ValueError):
        age = 30
    data["age"] = age
    data.setdefault("stance_bias", "")
    data.setdefault("voice_id", "")

    return GuestProfileOut(**data)


# ---------------------------------------------------------------------------
# GET /api/voices — built-in voice library
# ---------------------------------------------------------------------------

@router.get("/voices", response_model=VoiceLibraryResponse)
async def list_voices():
    """Return built-in MiniMax voice IDs grouped by gender plus the official voice picker URL."""
    from backend.agents.personas import VOICE_LIBRARY_BY_GENDER
    from backend.models import Gender

    return VoiceLibraryResponse(
        male=VOICE_LIBRARY_BY_GENDER[Gender.MALE],
        female=VOICE_LIBRARY_BY_GENDER[Gender.FEMALE],
        official_url="https://www.minimaxi.com/audio/voices",
    )


# ---------------------------------------------------------------------------
# Settings management endpoints
# ---------------------------------------------------------------------------

def _mask_key(key: str) -> str:
    """Return a masked version of an API key (show first 4 + last 4 chars)."""
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return key[:4] + "****" + key[-4:]


def _update_env_file(patch: "AppSettingsPatch") -> None:
    """Write non-None, non-masked patch values to .env file."""
    env_path = Path(".env")
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip().upper()] = v.strip()

    # Mapping from schema field to env var name (pydantic-settings convention = field UPPER)
    field_map: dict[str, str] = {
        "llm_base_url": "LLM_BASE_URL",
        "llm_api_key": "LLM_API_KEY",
        "llm_model": "LLM_MODEL",
        "tavily_api_key": "TAVILY_API_KEY",
        "minimax_api_key": "MINIMAX_API_KEY",
        "minimax_tts_model": "MINIMAX_TTS_MODEL",
        "minimax_tts_base_url": "MINIMAX_TTS_BASE_URL",
    }
    for field, env_key in field_map.items():
        value = getattr(patch, field, None)
        if value is not None and "****" not in str(value):
            existing[env_key] = str(value)

    lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.get("/settings", response_model=AppSettingsOut)
async def get_settings():
    """Return current application settings (API keys masked)."""
    return AppSettingsOut(
        llm_base_url=settings.llm_base_url,
        llm_api_key=_mask_key(settings.llm_api_key),
        llm_model=settings.llm_model,
        tavily_api_key=_mask_key(settings.tavily_api_key),
        minimax_api_key=_mask_key(settings.minimax_api_key),
        minimax_tts_model=settings.minimax_tts_model,
        minimax_tts_base_url=settings.minimax_tts_base_url,
        max_guests=settings.max_guests,
        cors_origins=settings.cors_origins,
    )


@router.patch("/settings")
async def update_settings(patch: AppSettingsPatch):
    """Write changed values to .env and hot-reload the settings singleton."""
    from backend import config as config_module

    _update_env_file(patch)
    # Hot-reload: replace the singleton with a freshly loaded instance
    config_module.settings = config_module.Settings()
    return {"status": "ok", "message": "设置已更新，服务配置已重新加载"}


@router.get("/settings/reveal/{key_name}")
async def reveal_api_key(key_name: str):
    """Return the unmasked API key (e.g., 'llm_api_key', 'tavily_api_key', 'minimax_api_key')."""
    key_mapping = {
        "llm_api_key": settings.llm_api_key,
        "tavily_api_key": settings.tavily_api_key,
        "minimax_api_key": settings.minimax_api_key,
    }
    if key_name not in key_mapping:
        raise HTTPException(status_code=400, detail="Invalid key name")

    value = key_mapping[key_name]
    if not value:
        raise HTTPException(status_code=404, detail="Key not configured")

    return {"value": value}

# ---------------------------------------------------------------------------
# GET /api/status/{task_id} — SSE progress stream
# ---------------------------------------------------------------------------


@router.get("/status/{task_id}")
async def task_status(task_id: str):
    """Stream task progress via Server-Sent Events."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def _event_stream():
        last_sent = ""
        while True:
            task = _tasks.get(task_id, {})
            current = json.dumps(task, ensure_ascii=False)
            if current != last_sent:
                yield f"data: {current}\n\n"
                last_sent = current
            if task.get("status") in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running background task."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    status = task.get("status")
    if status in ("completed", "failed", "cancelled"):
        return {"status": status, "message": "任务已结束"}

    job = _task_jobs.get(task_id)
    if job and not job.done():
        job.cancel()

    task.update({
        "status": "cancelled",
        "stage": "cancelled",
        "detail": "任务已终止",
    })
    return {"status": "cancelled", "message": "任务已终止"}


# ---------------------------------------------------------------------------
# GET /api/episodes — list episodes
# ---------------------------------------------------------------------------

@router.get("/episodes", response_model=list[EpisodeSummary])
async def list_episodes():
    """Return all generated episodes (sorted newest first)."""
    output_dir = settings.output_dir
    if not output_dir.exists():
        return []

    episodes: list[EpisodeSummary] = []
    for json_path in sorted(output_dir.glob("*.json"), reverse=True):
        try:
            ep = Episode.load_json(json_path)
            episodes.append(
                EpisodeSummary(
                    id=ep.id,
                    title=ep.title,
                    topic=ep.topic,
                    summary=ep.summary,
                    created_at=ep.created_at.isoformat(),
                    guests=ep.guests,
                    word_count=ep.word_count,
                    duration_seconds=ep.duration_seconds,
                    has_audio=ep.audio_path is not None and Path(
                        ep.audio_path).exists(),
                )
            )
        except Exception as exc:
            logger.warning("Failed to load episode %s: %s",
                           json_path.name, exc)
    return episodes


# ---------------------------------------------------------------------------
# GET /api/episodes/{id} — episode detail
# ---------------------------------------------------------------------------

@router.get("/episodes/{episode_id}", response_model=EpisodeDetail)
async def get_episode(episode_id: str):
    """Return full episode detail including dialogue."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    ep = Episode.load_json(json_path)
    return EpisodeDetail(
        id=ep.id,
        title=ep.title,
        topic=ep.topic,
        summary=ep.summary,
        created_at=ep.created_at.isoformat(),
        guests=ep.guests,
        word_count=ep.word_count,
        duration_seconds=ep.duration_seconds,
        has_audio=ep.audio_path is not None and Path(ep.audio_path).exists(),
        dialogue=[
            DialogueLineOut(
                speaker=d.speaker,
                text=d.text,
                emotion=d.emotion,
                speech_rate=d.speech_rate,
            )
            for d in ep.dialogue
        ],
        news_sources=[s.model_dump() for s in ep.news_sources],
        article=ep.article,
    )


# ---------------------------------------------------------------------------
# DELETE /api/episodes/{id} — delete episode and related artifacts
# ---------------------------------------------------------------------------

@router.delete("/episodes/{episode_id}")
async def delete_episode(episode_id: str):
    """Delete an episode JSON, audio file, and log files if they exist."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    audio_path: Path | None = None
    try:
        episode = Episode.load_json(json_path)
        if episode.audio_path:
            audio_path = Path(episode.audio_path)
    except Exception as exc:
        logger.warning(
            "Failed to parse episode %s before deletion: %s", episode_id, exc)

    removed_files: list[str] = []

    def _safe_unlink(path: Path):
        if not path.exists() or not path.is_file():
            return
        path.unlink()
        removed_files.append(path.name)

    _safe_unlink(json_path)

    if audio_path is not None:
        _safe_unlink(audio_path)

    logs_dir = settings.output_dir / "logs"
    _safe_unlink(logs_dir / f"{episode_id}.jsonl")
    _safe_unlink(logs_dir / f"{episode_id}.debug.jsonl")

    segments_dir = settings.output_dir / "segments" / episode_id
    if segments_dir.exists() and segments_dir.is_dir():
        for segment_file in segments_dir.glob("*"):
            _safe_unlink(segment_file)
            removed_files.append(str(segment_file))
        try:
            segments_dir.rmdir()
            removed_files.append(str(segments_dir))
        except OSError:
            pass

    return {
        "status": "ok",
        "episode_id": episode_id,
        "removed_files": removed_files,
        "message": "节目已删除",
    }


@router.get("/episodes/{episode_id}/segments/{line_index}/audio")
async def get_episode_segment_audio(episode_id: str, line_index: int):
    """Stream one dialogue segment audio file for real-time preview/playback."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    ep = Episode.load_json(json_path)
    if line_index < 0 or line_index >= len(ep.dialogue):
        raise HTTPException(status_code=404, detail="Segment not found")

    line = ep.dialogue[line_index]
    segment_path = Path(
        line.segment_audio_path) if line.segment_audio_path else None
    if segment_path is None or not segment_path.exists():
        fallback_dir = settings.output_dir / "segments" / episode_id
        wav_fallback = fallback_dir / f"{line_index:04d}.wav"
        mp3_fallback = fallback_dir / f"{line_index:04d}.mp3"
        if wav_fallback.exists():
            segment_path = wav_fallback
        elif mp3_fallback.exists():
            segment_path = mp3_fallback
        else:
            raise HTTPException(
                status_code=404, detail="Segment audio not available")

    suffix = segment_path.suffix.lower()
    media_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    filename_ext = "wav" if suffix == ".wav" else "mp3"

    return FileResponse(
        str(segment_path),
        media_type=media_type,
        filename=f"airoundtable_{episode_id}_segment_{line_index}.{filename_ext}",
    )


@router.post("/episodes/{episode_id}/segments/cleanup")
async def cleanup_episode_segments(episode_id: str):
    """Delete per-segment temp audio files after final audio confirmation."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    episode = Episode.load_json(json_path)
    removed_count = 0

    for line in episode.dialogue:
        if line.segment_audio_path:
            segment_path = Path(line.segment_audio_path)
            if segment_path.exists() and segment_path.is_file():
                segment_path.unlink()
                removed_count += 1
            line.segment_audio_path = None

    segments_dir = settings.output_dir / "segments" / episode_id
    if segments_dir.exists() and segments_dir.is_dir():
        for segment_file in segments_dir.glob("*"):
            if segment_file.is_file():
                segment_file.unlink()
                removed_count += 1
        try:
            segments_dir.rmdir()
        except OSError:
            pass

    episode.save_json(settings.ensure_output_dir())

    return {
        "status": "ok",
        "episode_id": episode_id,
        "removed_segments": removed_count,
        "message": "段音频已清理",
    }


# ---------------------------------------------------------------------------
# GET /api/episodes/{id}/audio — serve audio file
# ---------------------------------------------------------------------------

@router.get("/episodes/{episode_id}/audio")
async def get_episode_audio(episode_id: str):
    """Stream the episode audio file."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    ep = Episode.load_json(json_path)
    if not ep.audio_path or not Path(ep.audio_path).exists():
        raise HTTPException(status_code=404, detail="Audio not available")

    audio_path = Path(ep.audio_path)
    suffix = audio_path.suffix.lower()
    media_type = "audio/wav" if suffix == ".wav" else "audio/mpeg"
    filename_ext = "wav" if suffix == ".wav" else "mp3"

    return FileResponse(
        str(audio_path),
        media_type=media_type,
        filename=f"airoundtable_{episode_id}.{filename_ext}",
    )


# ---------------------------------------------------------------------------
# Knowledge base management endpoints
# ---------------------------------------------------------------------------

@router.get("/knowledge/stats")
async def knowledge_stats():
    """Return document counts for each knowledge base collection."""
    try:
        kb = get_knowledge_base()
        stats = kb.get_collection_stats()
        return {"status": "ok", "collections": stats}
    except Exception as exc:
        logger.error("KB stats error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/knowledge/query")
async def knowledge_query(
    text: str,
    collection: str = "background_material",
    top_k: int = 5,
):
    """Query the knowledge base for relevant documents."""
    try:
        kb = get_knowledge_base()
        results = await kb.query(text, top_k=top_k, collection=collection)
        return {"query": text, "collection": collection, "results": results}
    except Exception as exc:
        logger.error("KB query error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/knowledge/ingest-episode/{episode_id}")
async def ingest_episode_to_kb(episode_id: str):
    """Manually ingest an existing episode into the knowledge base."""
    json_path = settings.output_dir / f"{episode_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Episode not found")

    ep = Episode.load_json(json_path)
    try:
        kb = get_knowledge_base()
        await kb.ingest_episode(
            episode_id=ep.id,
            topic=ep.topic,
            summary=ep.summary,
            dialogue_lines=[
                {"speaker": d.speaker, "text": d.text}
                for d in ep.dialogue
            ],
            news_sources=[s.model_dump() for s in ep.news_sources],
        )
        return {"status": "ok", "episode_id": ep.id, "message": "Episode ingested"}
    except Exception as exc:
        logger.error("KB ingest error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
