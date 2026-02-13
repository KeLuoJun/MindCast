"""FastAPI route definitions."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.agents.orchestrator import PodcastOrchestrator
from backend.api.schemas import (
    DialogueLineOut,
    EpisodeDetail,
    EpisodeSummary,
    GenerateRequest,
    ScriptPreviewRequest,
    TaskCreatedResponse,
)
from backend.config import settings
from backend.knowledge import get_knowledge_base
from backend.models import DetailedInfo, Episode
from backend.services.run_logger import EpisodeRunLogger
from backend.services.news_service import get_news_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory task tracking (MVP — no persistent task store)
_tasks: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Debug endpoints — stage-by-stage backend verification
# ---------------------------------------------------------------------------

@router.get("/debug/news")
async def debug_news(max_results: int = 5):
    """Fetch daily news only (without topic/script/audio generation)."""
    service = get_news_service()
    items = await service.get_daily_ai_news(max_results=max_results)
    return {
        "count": len(items),
        "items": [item.model_dump() for item in items],
    }


@router.post("/debug/script")
async def debug_script_preview(req: ScriptPreviewRequest | None = None):
    """Run pipeline until dialogue generation (skip TTS and audio stitching)."""
    payload = req or ScriptPreviewRequest()
    orchestrator = PodcastOrchestrator()

    news_items = await orchestrator._news.get_daily_ai_news(
        max_results=payload.max_news_results
    )
    if not news_items:
        raise HTTPException(status_code=502, detail="No news items retrieved")

    topic = await orchestrator.host.select_topic(news_items)
    search_queries = topic.get("search_queries", [])[
        : payload.max_search_queries]

    detailed_info: list[DetailedInfo] = []
    for query in search_queries:
        detailed_info.append(await orchestrator._news.search_detail(query))

    plan = await orchestrator.host.plan_episode(
        topic,
        [info.model_dump() for info in detailed_info],
        [guest.persona.name for guest in orchestrator.guests],
    )

    episode = Episode(
        topic=plan.topic,
        title=plan.topic,
        summary=plan.summary,
        guests=[guest.persona.name for guest in orchestrator.guests],
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
        },
    )
    word_count = sum(len(line.text) for line in dialogue)

    orchestrator.host.reset_history()
    for guest in orchestrator.guests:
        guest.reset_history()

    return {
        "topic": plan.topic,
        "summary": plan.summary,
        "talking_points": plan.talking_points,
        "word_count": word_count,
        "line_count": len(dialogue),
        "news_count": len(news_items),
        "search_queries": search_queries,
        "generation_log_path": str(run_logger.log_path),
        "dialogue": [
            {
                "speaker": line.speaker,
                "text": line.text,
                "emotion": line.emotion,
            }
            for line in dialogue
        ],
    }


# ---------------------------------------------------------------------------
# POST /api/generate — trigger new episode
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=TaskCreatedResponse)
async def generate_episode(req: GenerateRequest | None = None):
    """Start generating a new podcast episode in the background."""
    task_id = f"task_{len(_tasks) + 1}"
    _tasks[task_id] = {"status": "started",
                       "stage": "initializing", "detail": "", "episode_id": None}

    async def _run():
        orchestrator = PodcastOrchestrator()

        async def _progress(stage: str, detail: str):
            _tasks[task_id].update({"stage": stage, "detail": detail})

        try:
            episode = await orchestrator.generate_episode(progress=_progress)
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
        filename=f"mindcast_{episode_id}.{filename_ext}",
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
