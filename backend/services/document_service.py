"""Document parsing and ChromaDB ingestion service for MindCast.

Supported formats:
- PDF  (.pdf)       — via pypdf
- DOCX (.docx)     — via python-docx
- DOC  (.doc)      — plain-text fallback (limited)
- TXT  (.txt / .text)
- Markdown (.md / .markdown)
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Maximum characters per chunk stored in ChromaDB
_CHUNK_SIZE = 800
# Overlap between adjacent chunks
_CHUNK_OVERLAP = 100


def _chunk_text(text: str, chunk_size: int = _CHUNK_SIZE, overlap: int = _CHUNK_OVERLAP) -> list[str]:
    """Split *text* into overlapping chunks of at most *chunk_size* characters."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap  # overlap for context continuity
        if end == len(text):
            break
    return chunks


def _parse_pdf(path: Path) -> str:
    """Extract plain text from a PDF file."""
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "pypdf is not installed. Run: pip install pypdf") from e

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        parts.append(text)
    return "\n\n".join(parts)


def _parse_docx(path: Path) -> str:
    """Extract plain text from a .docx file."""
    try:
        from docx import Document  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "python-docx is not installed. Run: pip install python-docx") from e

    doc = Document(str(path))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n\n".join(paragraphs)


def _parse_text(path: Path) -> str:
    """Read a plain-text or Markdown file."""
    for encoding in ("utf-8", "gbk", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


def parse_document(path: Path) -> str:
    """Dispatch to the correct parser based on file extension.

    Returns the extracted plain text.
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    if suffix in (".docx",):
        return _parse_docx(path)
    if suffix in (".doc",):
        # Binary .doc requires python-docx which can't handle old binary format well;
        # fall back to decode as text with replacement (best-effort)
        logger.warning(
            ".doc format has limited support; consider converting to .docx")
        return _parse_text(path)
    if suffix in (".txt", ".text", ".md", ".markdown"):
        return _parse_text(path)
    # Unknown format — attempt text read
    logger.warning(
        "Unknown file format %s, attempting plain-text read", suffix)
    return _parse_text(path)


class DocumentService:
    """Upload, parse, chunk, and index documents into the knowledge base."""

    # Upload staging directory (relative to project root)
    UPLOAD_DIR: Path = Path("data/uploads")

    def __init__(self) -> None:
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    async def ingest_files(
        self,
        file_paths: list[Path],
        *,
        session_id: str | None = None,
        filenames: list[str] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Parse *file_paths*, chunk, and store in ChromaDB under a session.

        Parameters
        ----------
        file_paths:
            Absolute paths to the uploaded files (already saved to disk).
        session_id:
            Optional caller-supplied session ID (UUID). If *None*, a new
            one is created.
        filenames:
            Original filenames corresponding to each path, used as metadata.

        Returns
        -------
        session_id, list of ingestion info dicts (one per file).
        """
        from backend.knowledge import get_knowledge_base
        from backend.knowledge.chroma_kb import BACKGROUND_MATERIAL, KNOWLEDGE_SCOPE_TASK

        if session_id is None:
            session_id = uuid.uuid4().hex

        kb = get_knowledge_base()
        infos: list[dict[str, Any]] = []

        for i, path in enumerate(file_paths):
            fname = (filenames[i] if filenames and i <
                     len(filenames) else path.name)
            logger.info("Parsing document: %s (%s)", fname, path.suffix)
            try:
                raw_text = parse_document(path)
            except Exception as exc:
                logger.error("Failed to parse %s: %s", fname, exc)
                infos.append({"filename": fname, "status": "error",
                             "error": str(exc), "chunks": 0})
                continue

            chunks = _chunk_text(raw_text)
            if not chunks:
                logger.warning("No text extracted from %s", fname)
                infos.append(
                    {"filename": fname, "status": "empty", "chunks": 0})
                continue

            docs = [
                {
                    "content": chunk,
                    "metadata": {
                        "source_filename": fname,
                        "chunk_index": j,
                        "total_chunks": len(chunks),
                        "session_id": session_id,
                    },
                }
                for j, chunk in enumerate(chunks)
            ]

            try:
                stored = await kb.store_many(
                    docs,
                    collection=BACKGROUND_MATERIAL,
                    scope=KNOWLEDGE_SCOPE_TASK,
                    task_id=session_id,
                )
                logger.info(
                    "Stored %d chunks from '%s' (session=%s)", stored, fname, session_id
                )
                infos.append({"filename": fname, "status": "ok",
                             "chunks": stored, "char_count": len(raw_text)})
            except Exception as exc:
                logger.error("Failed to store chunks for %s: %s", fname, exc)
                infos.append({"filename": fname, "status": "error",
                             "error": str(exc), "chunks": 0})

        return session_id, infos

    async def get_document_summary(self, session_id: str, max_chars: int = 3000) -> str:
        """Return a concatenated sample of the session's uploaded documents."""
        from backend.knowledge import get_knowledge_base
        from backend.knowledge.chroma_kb import BACKGROUND_MATERIAL, KNOWLEDGE_SCOPE_TASK

        kb = get_knowledge_base()
        # Use a broad query to fetch varied chunks
        docs = await kb.query(
            "文档内容摘要概述",
            top_k=8,
            collection=BACKGROUND_MATERIAL,
            scope=KNOWLEDGE_SCOPE_TASK,
            task_id=session_id,
        )
        if not docs:
            # Try with None scope to catch them anyway
            docs = await kb.query(
                "文档内容",
                top_k=8,
                collection=BACKGROUND_MATERIAL,
                scope=None,
                task_id=session_id,
            )
        snippets = [d.get("content", "")[:300]
                    for d in docs if d.get("content")]
        combined = "\n\n".join(snippets)
        return combined[:max_chars]


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_instance: DocumentService | None = None


def get_document_service() -> DocumentService:
    """Return (or lazily create) the singleton DocumentService."""
    global _instance
    if _instance is None:
        _instance = DocumentService()
    return _instance
