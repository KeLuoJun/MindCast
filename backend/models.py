"""Core data models for MindCast."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# News
# ---------------------------------------------------------------------------

class NewsItem(BaseModel):
    """A single news article returned by Tavily."""
    title: str
    url: str
    content: str
    published_date: str | None = None
    score: float | None = None


class DetailedInfo(BaseModel):
    """Detailed search result for a specific query."""
    query: str
    answer: str | None = None
    results: list[NewsItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Persona / Agent
# ---------------------------------------------------------------------------

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class PersonaConfig(BaseModel):
    """Definition of a podcast persona (host or guest)."""
    name: str
    gender: Gender
    age: int
    mbti: str
    personality: str
    occupation: str
    speaking_style: str
    stance_bias: str = ""
    voice_id: str
    background: str  # life experience / expertise


# ---------------------------------------------------------------------------
# Dialogue
# ---------------------------------------------------------------------------

class DialogueLine(BaseModel):
    """A single line of podcast dialogue with TTS annotations."""
    speaker: str
    text: str               # raw text for display
    ssml_text: str           # text with TTS annotations (<#x#>, (laughs) etc.)
    emotion: str = "neutral"  # emotion hint for voice_setting
    voice_id: str = ""
    pause_before: float = 0.0  # seconds
    pause_after: float = 0.3   # seconds


# ---------------------------------------------------------------------------
# Episode
# ---------------------------------------------------------------------------

class EpisodePlan(BaseModel):
    """Structured outline planned by the host agent."""
    topic: str
    summary: str
    talking_points: list[str | dict[str, Any]] = Field(default_factory=list)
    opening: str | dict[str, Any] = ""
    closing: str | dict[str, Any] = ""
    key_questions: list[str] = Field(default_factory=list)
    unexpected_angle: str = ""

    def opening_text(self) -> str:
        if isinstance(self.opening, str):
            return self.opening
        return str(self.opening.get("hook") or self.opening.get("stance_hint") or "")

    def closing_text(self) -> str:
        if isinstance(self.closing, str):
            return self.closing
        return str(self.closing.get("open_question") or self.closing.get("host_takeaway") or "")

    def talking_point_text(self, index: int) -> str:
        if index < 0 or index >= len(self.talking_points):
            return ""
        point = self.talking_points[index]
        if isinstance(point, str):
            return point
        return str(point.get("point") or "")

    def talking_point_depth_hint(self, index: int) -> str:
        if index < 0 or index >= len(self.talking_points):
            return ""
        point = self.talking_points[index]
        if isinstance(point, dict):
            return str(point.get("depth_hint") or "")
        return ""

    def talking_point_conflict_setup(self, index: int) -> str:
        if index < 0 or index >= len(self.talking_points):
            return ""
        point = self.talking_points[index]
        if isinstance(point, dict):
            return str(point.get("conflict_setup") or "")
        return ""

    def talking_point_texts(self) -> list[str]:
        return [self.talking_point_text(i) for i in range(len(self.talking_points)) if self.talking_point_text(i)]


class Episode(BaseModel):
    """A complete podcast episode."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = ""
    topic: str = ""
    summary: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    guests: list[str] = Field(default_factory=list)
    dialogue: list[DialogueLine] = Field(default_factory=list)
    news_sources: list[NewsItem] = Field(default_factory=list)
    audio_path: str | None = None
    generation_log_path: str | None = None
    duration_seconds: float | None = None
    word_count: int = 0

    def save_json(self, output_dir: Path) -> Path:
        """Persist episode metadata as JSON."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{self.id}.json"
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")
        return path

    @classmethod
    def load_json(cls, path: Path) -> "Episode":
        """Load an episode from a JSON file."""
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
