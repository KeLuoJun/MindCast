"""API request / response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request body for triggering a new episode generation."""
    # MVP: no extra params needed — future: topic hints, guest selection, etc.
    pass


class ScriptPreviewRequest(BaseModel):
    """Request body for previewing script generation without TTS/audio."""
    max_news_results: int = Field(default=6, ge=3, le=10)
    max_search_queries: int = Field(default=3, ge=1, le=5)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class TaskCreatedResponse(BaseModel):
    """Returned when a background generation task is created."""
    task_id: str
    message: str = "播客生成任务已创建"


class EpisodeSummary(BaseModel):
    """Lightweight episode info for list views."""
    id: str
    title: str
    topic: str
    summary: str
    created_at: str
    guests: list[str]
    word_count: int
    duration_seconds: float | None
    has_audio: bool


class DialogueLineOut(BaseModel):
    """Single dialogue line for display."""
    speaker: str
    text: str
    emotion: str


class EpisodeDetail(BaseModel):
    """Full episode data including dialogue."""
    id: str
    title: str
    topic: str
    summary: str
    created_at: str
    guests: list[str]
    word_count: int
    duration_seconds: float | None
    has_audio: bool
    dialogue: list[DialogueLineOut]
    news_sources: list[dict]
