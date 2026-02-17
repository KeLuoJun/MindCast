"""API request / response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request body for triggering a new episode generation."""
    topic: str = ""
    selected_guests: list[str] = Field(default_factory=list, max_length=3)


class ScriptPreviewRequest(BaseModel):
    """Request body for previewing script generation without TTS/audio."""
    max_news_results: int = Field(default=6, ge=3, le=10)
    max_search_queries: int = Field(default=3, ge=1, le=5)
    topic: str = ""
    selected_guests: list[str] = Field(default_factory=list, max_length=3)


class GuestProfileIn(BaseModel):
    """User-defined guest profile input."""
    name: str
    gender: str
    age: int = Field(ge=18, le=90)
    mbti: str
    personality: str
    occupation: str
    speaking_style: str
    stance_bias: str = ""
    voice_id: str = ""
    background: str


class GuestProfileOut(BaseModel):
    """Guest profile payload returned to frontend."""
    name: str
    gender: str
    age: int
    mbti: str
    personality: str
    occupation: str
    speaking_style: str
    stance_bias: str = ""
    voice_id: str = ""
    background: str


class ScriptLineIn(BaseModel):
    """Editable dialogue line submitted by frontend before synthesis."""
    speaker: str
    text: str
    emotion: str = "neutral"
    voice_id: str | None = None


class ScriptSynthesisRequest(BaseModel):
    """Request body for synthesizing audio from an edited script."""
    title: str = ""
    topic: str = ""
    summary: str = ""
    guests: list[str] = Field(default_factory=list)
    dialogue: list[ScriptLineIn] = Field(default_factory=list)
    news_sources: list[dict] = Field(default_factory=list)


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
