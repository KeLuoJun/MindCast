# MindCast — Copilot Instructions

Multi-agent AI podcast generator (AI圆桌派). Fetches AI news via Tavily, generates Chinese dialogue with 4 LangGraph agents, synthesizes voice with MiniMax TTS, serves via FastAPI + Vue 3.

## Architecture

```
News (Tavily) → Host selects topic → Deep research (RAG-first, Tavily fallback)
→ RAG retrieval (ChromaDB) → Episode plan → Dialogue generation → TTS → Audio stitch → Save
```

- **Backend**: `backend/` — FastAPI app, LangGraph pipeline, agents, services
- **Frontend**: `frontend/src/` — Vue 3 + Vite, Composition API (`<script setup>`)
- **Pipeline entry**: [`backend/agents/orchestrator.py`](../backend/agents/orchestrator.py) — `OrchestratorState` TypedDict, compiled graph reused across runs
- **API entry**: [`backend/api/routes.py`](../backend/api/routes.py) — `APIRouter(prefix="/api")`
- **Config**: [`backend/config.py`](../backend/config.py) — single `Settings` singleton via `pydantic_settings`; always import `from backend.config import settings`

## Build & Test

```bash
# Backend
pip install -e .
python main.py                    # uvicorn with reload

# Frontend
cd frontend && npm install && npm run dev   # http://localhost:5173

# Run scripts
python scripts/run_text_pipeline.py

# Tests
pytest tests/
```

**Prerequisites**: Python 3.13+, Node 18+, `ffmpeg` on PATH, `.env` with `DEEPSEEK_API_KEY`, `TAVILY_API_KEY`, `MINIMAX_API_KEY`, `MINIMAX_GROUP_ID`.

## Code Conventions

**Singleton services** — never instantiate directly; use factory functions:
```python
from backend.services.llm_service import get_llm_service
llm = get_llm_service()
```
Same pattern for `TTSService`, `NewsService`, `GuestPoolService`.

**LLM outputs are always JSON** — ask the LLM for raw JSON (no markdown fences), parse with `json.loads()` after stripping fences, fall back gracefully. See `HostAgent.select_topic()` in [`backend/agents/host.py`](../backend/agents/host.py).

**LangGraph nodes return partial dicts** — only return updated keys from each node, not the full `OrchestratorState`.

**Episode IDs** are 12-char hex: `uuid.uuid4().hex[:12]`. Files: `output/episodes/{id}.json`, `{id}.wav`, `output/episodes/logs/{id}.jsonl`.

**No database** — episodes stored as JSON files in `output/episodes/`, loaded by globbing `*.json`. Guest pool: `data/guest_pool.json`.

**Tasks are fire-and-forget** — `asyncio.create_task()` with in-memory `_tasks: dict`; never persist task state.

## Data Models

All models in [`backend/models.py`](../backend/models.py) use `pydantic.BaseModel`.

- `EpisodePlan.talking_points` can be `list[str]` or `list[dict]` — always use accessor methods: `.talking_point_text(i)`, `.talking_point_depth_hint(i)`.
- `DialogueLine.ssml_text` uses MiniMax-specific markup: `<#0.5#>` for 0.5s pause, `(笑)` / `(叹气)` for interjections.
- Personas defined in [`backend/agents/personas.py`](../backend/agents/personas.py) — system prompts include banned AI-writing patterns (e.g., "此外", "赋能", "值得注意的是").

## Integration Points

| Service | Config key | Notes |
|---|---|---|
| LLM | `llm_base_url` (DeepSeek), `llm_api_key` | OpenAI-compatible SDK; model `deepseek-chat` |
| TTS | `minimax_api_key`, `minimax_group_id` | HTTP POST to MiniMax T2A v2; response is hex-encoded audio |
| News | `tavily_api_key` | `tavily-python` client |
| RAG | ChromaDB local | Persisted at `data/chromadb/`; collections: `BACKGROUND_MATERIAL`, `KNOWLEDGE_SCOPE_GLOBAL` |

**SSE progress**: `GET /api/status/{task_id}` streams `text/event-stream`; set `Cache-Control: no-cache` and `X-Accel-Buffering: no` on the response.

## Language

- All dialogue, progress messages, system prompts, and user-facing text are **Chinese**.
- English only for AI/tech proper nouns (e.g., LangGraph, ChromaDB).
- Frontend brand name: "AI圆桌派"; stack credit: "基于 LangGraph + MiniMax TTS".
