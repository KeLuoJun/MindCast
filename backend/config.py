"""MindCast configuration management via Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (OpenAI-compatible) ---
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"

    # --- Tavily ---
    tavily_api_key: str = ""

    # --- MiniMax TTS ---
    minimax_api_key: str = ""
    minimax_tts_model: str = "speech-2.8-hd"
    minimax_tts_base_url: str = "https://api.minimaxi.com/v1/t2a_v2"

    # --- Podcast parameters ---
    max_guests: int = 3
    episode_duration_minutes: int = 5
    target_word_count_min: int = 1500
    target_word_count_max: int = 2000
    output_dir: Path = Path("output/episodes")

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:5173", "http://localhost:3000"]

    def ensure_output_dir(self) -> Path:
        """Create output directory if it does not exist and return it."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir


# Singleton instance
settings = Settings()
