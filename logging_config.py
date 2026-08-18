"""
logging_config.py - Logging setup for NutriVision.

Call `setup_logging()` once at application startup to configure
console and optional file logging for all modules.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    fmt: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
) -> None:
    """
    Configure logging for the entire application.

    Args:
        level: Logging level (default: INFO).
        log_file: Optional path to a log file. If provided, logs will also
                  be written to this file.
        fmt: Log message format string.
    """
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(str(log_path), encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format=fmt,
        handlers=handlers,
    )

    # Quiet down noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

