"""Persistent guest pool management for user-defined podcast guests."""

from __future__ import annotations

import json
from pathlib import Path

from backend.agents.personas import GUEST_PERSONAS
from backend.models import Gender, PersonaConfig


class GuestPoolService:
    """CRUD service for guest profiles persisted as JSON."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self.storage_path = storage_path or Path("data/guest_pool.json")

    def _ensure_parent_dir(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _default_guests(self) -> list[PersonaConfig]:
        return [p.model_copy(deep=True) for p in GUEST_PERSONAS]

    def list_guests(self) -> list[PersonaConfig]:
        if not self.storage_path.exists():
            guests = self._default_guests()
            self.save_guests(guests)
            return guests

        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            guests = [PersonaConfig.model_validate(item) for item in raw]
            if not guests:
                guests = self._default_guests()
                self.save_guests(guests)
            return guests
        except Exception:
            guests = self._default_guests()
            self.save_guests(guests)
            return guests

    def save_guests(self, guests: list[PersonaConfig]) -> None:
        self._ensure_parent_dir()
        payload = [guest.model_dump(mode="json") for guest in guests]
        self.storage_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_guest(self, guest: PersonaConfig) -> list[PersonaConfig]:
        guests = self.list_guests()
        if any(existing.name == guest.name for existing in guests):
            raise ValueError(f"Guest '{guest.name}' already exists")
        guests.append(guest)
        self.save_guests(guests)
        return guests

    def update_guest(self, original_name: str, updated: PersonaConfig) -> list[PersonaConfig]:
        guests = self.list_guests()
        target_index = next(
            (index for index, guest in enumerate(
                guests) if guest.name == original_name),
            None,
        )
        if target_index is None:
            raise ValueError(f"Guest '{original_name}' not found")

        if (
            updated.name != original_name
            and any(existing.name == updated.name for existing in guests)
        ):
            raise ValueError(f"Guest '{updated.name}' already exists")

        guests[target_index] = updated
        self.save_guests(guests)
        return guests

    def delete_guest(self, name: str) -> list[PersonaConfig]:
        guests = self.list_guests()
        filtered = [guest for guest in guests if guest.name != name]
        if len(filtered) == len(guests):
            raise ValueError(f"Guest '{name}' not found")
        self.save_guests(filtered)
        return filtered


_guest_pool_service: GuestPoolService | None = None


def get_guest_pool_service() -> GuestPoolService:
    global _guest_pool_service
    if _guest_pool_service is None:
        _guest_pool_service = GuestPoolService()
    return _guest_pool_service


def to_persona_config(payload: dict) -> PersonaConfig:
    gender_value = str(payload.get("gender", "")).strip().lower()
    if gender_value not in {Gender.MALE.value, Gender.FEMALE.value}:
        raise ValueError("gender must be 'male' or 'female'")

    mbti = str(payload.get("mbti", "")).strip().upper()
    if len(mbti) != 4:
        raise ValueError("mbti must be a 4-letter code")

    return PersonaConfig(
        name=str(payload.get("name", "")).strip(),
        gender=Gender(gender_value),
        age=int(payload.get("age", 30)),
        mbti=mbti,
        personality=str(payload.get("personality", "")).strip(),
        occupation=str(payload.get("occupation", "")).strip(),
        speaking_style=str(payload.get("speaking_style", "")).strip(),
        stance_bias=str(payload.get("stance_bias", "")).strip(),
        voice_id=str(payload.get("voice_id", "")).strip(),
        background=str(payload.get("background", "")).strip(),
    )
