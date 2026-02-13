"""Centralized logging configuration for MindCast.

Log format:
[2026-01-21 22:03:19] INFO [module.function:38] message

Components:
│ 时间戳               │级别│ 模块名.函数名:行号      │ 日志消息
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Custom formatter
# ---------------------------------------------------------------------------

LOG_FORMAT = "[%(asctime)s] %(levelname)-5s [%(module)s.%(funcName)s:%(lineno)d] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Separator line for visual clarity in logs
SEPARATOR = "=" * 50


class MindCastFormatter(logging.Formatter):
    """Custom formatter that produces the standard MindCast log format.

    Output example:
        [2026-01-21 22:03:19] INFO  [orchestrator.generate_episode:38] Starting pipeline
    """

    def __init__(self) -> None:
        super().__init__(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


# ---------------------------------------------------------------------------
# Setup helpers
# ---------------------------------------------------------------------------


def setup_logging(
    *,
    level: int = logging.INFO,
    log_file: str | Path | None = None,
    enable_console: bool = True,
) -> None:
    """Configure the root logger with *MindCast* format.

    Parameters
    ----------
    level:
        Minimum log level (default INFO).
    log_file:
        Optional path to a log file.  A ``FileHandler`` will be added.
    enable_console:
        Whether to add a ``StreamHandler`` to *stderr* (default True).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Remove any pre-existing handlers to avoid duplicate output
    root.handlers.clear()

    formatter = MindCastFormatter()

    if enable_console:
        console = logging.StreamHandler(sys.stderr)
        console.setLevel(level)
        console.setFormatter(formatter)
        root.addHandler(console)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(str(log_path), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def get_episode_file_handler(episode_id: str, output_dir: Path) -> logging.FileHandler:
    """Create a file handler for a specific episode's generation log.

    Returns a ``FileHandler`` that writes *DEBUG*-level logs to
    ``<output_dir>/logs/<episode_id>.log``.
    """
    log_path = output_dir / "logs" / f"{episode_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(str(log_path), encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(MindCastFormatter())
    return handler
