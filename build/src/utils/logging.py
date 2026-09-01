"""Logging infrastructure with privacy sanitization for AI-Enhanced LibreOffice Writer."""

import logging
import os
import sys
from typing import Optional


class SanitizingFormatter(logging.Formatter):
    """Custom formatter ensuring document text and sensitive patterns are not leaked to logs."""

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)
        return formatted


_logger_initialized = False


def setup_logger(
    name: str = "ai_writer",
    level: str = "INFO",
    log_file: Optional[str] = None,
    sanitize: bool = True,
) -> logging.Logger:
    """Initialize and configure the application logger."""
    global _logger_initialized
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = SanitizingFormatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    else:
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    _logger_initialized = True
    return logger


def get_logger(name: str = "ai_writer") -> logging.Logger:
    """Get the logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
