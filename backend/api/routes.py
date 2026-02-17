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
    DialogueLineOut,
    EpisodeDetail,
    EpisodeSummary,
    GuestProfileIn,
    GuestProfileOut,
    GenerateRequest,
    ScriptSynthesisRequest,
    ScriptPreviewRequest,
    TaskCreatedResponse,
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

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory task tracking (MVP — no persistent task store)
_tasks: dict[str, dict] = {}


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
async def debug_news(max_results: int = 10):
    """Fetch daily news only (without topic/script/audio generation)."""
    from backend.services.llm_service import get_llm_service

    service = get_news_service()
    items = await service.get_daily_ai_news(max_results=max_results)

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

    news_items = await orchestrator._news.get_daily_ai_news(
        max_results=payload.max_news_results
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
        except Exception as exc:
            logger.exception("Script synthesis failed")
            _tasks[task_id].update({
                "status": "failed",
                "stage": "error",
                "detail": str(exc),
            })

    asyncio.create_task(_run())
    return TaskCreatedResponse(task_id=task_id, message="语音合成任务已创建")


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
        except Exception as exc:
            logger.exception("Episode generation failed")
            _tasks[task_id].update({
                "status": "failed",
                "stage": "error",
                "detail": str(exc),
            })

    asyncio.create_task(_run())
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
            if task.get("status") in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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
            DialogueLineOut(speaker=d.speaker, text=d.text, emotion=d.emotion)
            for d in ep.dialogue
        ],
        news_sources=[s.model_dump() for s in ep.news_sources],
    )


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
