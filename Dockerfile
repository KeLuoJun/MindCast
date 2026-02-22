# ── Stage 1: dependency installer (uses uv for fast resolution) ──────────────
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

WORKDIR /app

# Copy dependency manifests first (better layer caching)
COPY pyproject.toml uv.lock* ./

# Install dependencies into an isolated virtual env
RUN uv sync --frozen --no-install-project --no-dev

# ── Stage 2: runtime ──────────────────────────────────────────────────────────
FROM python:3.13-slim-bookworm AS runtime

# Install ffmpeg (required by pydub for audio stitching)
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy virtual env from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY main.py ./
COPY backend/ ./backend/

# Ensure runtime directories exist
RUN mkdir -p output/episodes/logs data/chromadb

EXPOSE 8000

# Use exec form so signals (SIGTERM) propagate correctly
CMD ["python", "main.py"]
