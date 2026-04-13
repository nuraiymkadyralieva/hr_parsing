"""Logger configuration helpers for the HR parser project."""

from __future__ import annotations

import logging


def setup_logger() -> logging.Logger:
    """Create and configure the project logger without duplicate handlers."""
    logger = logging.getLogger("hr_parser")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.propagate = False
    return logger
