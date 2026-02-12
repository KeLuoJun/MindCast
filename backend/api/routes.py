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
    TaskCreatedResponse,
)
from backend.config import settings
from backend.models import Episode

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

# In-memory task tracking (MVP — no persistent task store)
_tasks: dict[str, dict] = {}


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

    return FileResponse(
        ep.audio_path,
        media_type="audio/mpeg",
        filename=f"mindcast_{episode_id}.mp3",
    )
