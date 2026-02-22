"""Persistent host persona management."""

from __future__ import annotations

import json
from pathlib import Path

from backend.agents.personas import HOST_PERSONA
from backend.models import PersonaConfig


class HostService:
    """CRUD service for the host profile persisted as JSON."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path("data/host.json")

    def _ensure_parent_dir(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _default_host(self) -> PersonaConfig:
        return HOST_PERSONA.model_copy(deep=True)

    def get_host(self) -> PersonaConfig:
        if not self.storage_path.exists():
            host = self._default_host()
            self.save_host(host)
            return host

        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            return PersonaConfig.model_validate(raw)
        except Exception:
            host = self._default_host()
            self.save_host(host)
            return host

    def save_host(self, host: PersonaConfig) -> PersonaConfig:
        self._ensure_parent_dir()
        payload = host.model_dump(mode="json")
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return host


_host_service: HostService | None = None


def get_host_service() -> HostService:
    global _host_service
    if _host_service is None:
        _host_service = HostService()
    return _host_service
