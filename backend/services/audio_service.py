"""Audio stitching service — combine TTS segments into a complete episode."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from pydub import AudioSegment

logger = logging.getLogger(__name__)


class AudioService:
    """Stitch individual TTS audio segments into a final MP3 episode."""

    async def stitch_episode(
        self,
        audio_segments: list[tuple[bytes, float]],
        output_path: str,
        *,
        target_dbfs: float = -20.0,
    ) -> float:
        """Concatenate audio segments with pauses and normalize volume.

        Parameters
        ----------
        audio_segments:
            List of ``(mp3_bytes, pause_after_seconds)`` tuples.
        output_path:
            Destination file path for the final MP3.
        target_dbfs:
            Target loudness for volume normalization.

        Returns
        -------
        float
            Duration of the final audio in seconds.
        """
        combined = AudioSegment.silent(duration=0)

        for idx, (mp3_bytes, pause_after) in enumerate(audio_segments):
            if not mp3_bytes:
                logger.warning("Segment %d has empty audio, skipping.", idx)
                continue
            try:
                segment = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))

                # Volume normalization
                if segment.dBFS != float("-inf"):
                    change = target_dbfs - segment.dBFS
                    segment = segment.apply_gain(change)

                combined += segment

                # Insert pause between segments
                pause_ms = int(max(pause_after, 0.1) * 1000)
                combined += AudioSegment.silent(duration=pause_ms)

            except Exception as exc:
                logger.error(
                    "Failed to process audio segment %d: %s", idx, exc)
                continue

        if len(combined) == 0:
            raise RuntimeError("No valid audio segments to stitch")

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Export final MP3
        combined.export(output_path, format="mp3", bitrate="128k")
        duration_seconds = len(combined) / 1000.0
        logger.info(
            "Exported episode: %s (%.1f seconds)", output_path, duration_seconds
        )
        return duration_seconds


# Module-level convenience instance
audio_service = AudioService()
