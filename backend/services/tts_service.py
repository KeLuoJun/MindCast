"""MiniMax TTS service — speech-2.8-hd HTTP synthesis."""

from __future__ import annotations

import logging

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Synthesize speech via MiniMax T2A HTTP API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.minimax_api_key
        self.model = model or settings.minimax_tts_model
        self.base_url = base_url or settings.minimax_tts_base_url

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        emotion: str | None = None,
        *,
        speed: float = 1.0,
        vol: float = 1.0,
        pitch: int = 0,
        sample_rate: int = 32000,
        bitrate: int = 128000,
        retries: int = 3,
    ) -> bytes:
        """Synthesize a single text segment and return raw MP3 bytes.

        The *text* may contain MiniMax inline annotations such as
        ``<#0.5#>`` for pauses and ``(laughs)`` for interjections.
        """
        if not text.strip():
            return b""

        # Truncate to API limit
        if len(text) > 10000:
            logger.warning("Text exceeds 10 000 chars, truncating.")
            text = text[:10000]

        voice_setting: dict = {
            "voice_id": voice_id,
            "speed": speed,
            "vol": vol,
            "pitch": pitch,
        }
        if emotion and emotion != "neutral":
            voice_setting["emotion"] = emotion

        payload = {
            "model": self.model,
            "text": text,
            "stream": False,
            "voice_setting": voice_setting,
            "audio_setting": {
                "sample_rate": sample_rate,
                "bitrate": bitrate,
                "format": "mp3",
                "channel": 1,
            },
            "language_boost": "Chinese",
            "output_format": "hex",
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_error: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        self.base_url,
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                # Check API-level errors
                base_resp = data.get("base_resp", {})
                if base_resp.get("status_code", 0) != 0:
                    raise RuntimeError(
                        f"MiniMax API error: {base_resp.get('status_msg', 'unknown')}"
                    )

                hex_audio = data.get("data", {}).get("audio", "")
                if not hex_audio:
                    raise RuntimeError("Empty audio data in MiniMax response")

                audio_bytes = bytes.fromhex(hex_audio)
                logger.info(
                    "TTS synthesized %d bytes for voice=%s", len(
                        audio_bytes), voice_id
                )
                return audio_bytes

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "TTS attempt %d/%d failed: %s", attempt, retries, exc
                )

        raise RuntimeError(
            f"TTS failed after {retries} retries") from last_error


# Module-level convenience instance (lazy)
_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


tts_service: TTSService | None = None  # type: ignore[assignment]
