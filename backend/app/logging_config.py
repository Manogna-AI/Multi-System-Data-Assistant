"""
Structured Logging Configuration — JSON format for production observability.

Uses python-json-logger for structured JSON log output to stdout.
This makes logs parseable by log aggregation tools (ELK, CloudWatch, etc.).

Requirements:
    pip install python-json-logger

References:
    - python-json-logger: https://github.com/madzak/python-json-logger
"""

from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger


def configure_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for the application.

    Sets up a single StreamHandler writing JSON-formatted logs to stdout.
    Clears any existing handlers to prevent duplicate log entries.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to INFO.
    """
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)