"""MindCast — Multi-Agent AI Podcast Generator (FastAPI entry point)."""

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes import router
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="MindCast API",
    description="Multi-Agent AI Podcast Generator",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(router)

# Serve generated episode files
output_dir = settings.ensure_output_dir()
app.mount("/static/episodes",
          StaticFiles(directory=str(output_dir)), name="episodes")


@app.get("/")
async def root():
    return {"name": "MindCast API", "version": "0.1.0", "status": "running"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host,
                port=settings.port, reload=True)
