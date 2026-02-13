"""Structured run logger for full podcast generation trace."""

from __future__ import annotations

import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


class EpisodeRunLogger:
    """Write end-to-end generation logs to a JSONL file."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._seq = 0

    def event(
        self,
        stage: str,
        message: str,
        *,
        status: str = "info",
        payload: Any | None = None,
    ) -> None:
        """Append a structured log event."""
        self._seq += 1
        item: dict[str, Any] = {
            "seq": self._seq,
            "ts": datetime.now().isoformat(),
            "stage": stage,
            "status": status,
            "message": message,
        }
        if payload is not None:
            item["payload"] = payload

        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    def exception(self, stage: str, exc: Exception, *, payload: Any | None = None) -> None:
        """Append an exception event with traceback."""
        trace = traceback.format_exc()
        merged_payload: dict[str, Any] = {
            "error_type": exc.__class__.__name__,
            "error": str(exc),
            "traceback": trace,
        }
        if payload is not None:
            merged_payload["context"] = payload
        self.event(stage, "pipeline exception",
                   status="error", payload=merged_payload)
