"""Logging configuration for extended_google_doc_utils."""

import logging
import os
import sys
from typing import Optional


# Package logger name
LOGGER_NAME = "extended_google_doc_utils"

# Default format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger for the package or a submodule.

    Args:
        name: Optional submodule name. If provided, returns a child logger
              (e.g., "extended_google_doc_utils.auth"). If None, returns
              the root package logger.

    Returns:
        logging.Logger: Configured logger instance
    """
    if name:
        return logging.getLogger(f"{LOGGER_NAME}.{name}")
    return logging.getLogger(LOGGER_NAME)


def setup_logging(
    level: int = logging.INFO,
    format_string: str = DEFAULT_FORMAT,
    date_format: str = DEFAULT_DATE_FORMAT,
    stream: Optional[object] = None,
) -> logging.Logger:
    """Configure logging for the package.

    Args:
        level: Logging level (default: logging.INFO)
        format_string: Log message format
        date_format: Date format for log timestamps
        stream: Output stream (default: sys.stderr)

    Returns:
        logging.Logger: Configured root package logger
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setLevel(level)
        formatter = logging.Formatter(format_string, datefmt=date_format)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def setup_logging_from_env() -> logging.Logger:
    """Configure logging based on environment variables.

    Environment variables:
        LOG_LEVEL: Logging level name (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                   Default: INFO

    Returns:
        logging.Logger: Configured root package logger
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    return setup_logging(level=level)
