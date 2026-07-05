"""
Centralized logger utility for the personal_finance project.

Usage:
    from utils.logger import get_logger

    logger = get_logger(__name__)
    logger.info("Something happened", extra={"user": request.user.username})
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger instance for the given module name.

    All configuration is handled by the LOGGING dict in settings.py.
    This function exists purely as a convenience import — it delegates
    to `logging.getLogger()` so that Django's LOGGING config takes effect.

    The reason for a wrapper (rather than calling logging.getLogger directly)
    is to allow future enhancements (e.g., injecting request context, adding
    default extra fields) without changing every caller.
    """
    return logging.getLogger(name)


# Convenience aliases for common log levels
# These reduce the mental overhead of remembering Python's log level hierarchy.
# Usage: logger.log(INFO, "message") — not needed, just use logger.info()
# Kept for completeness and potential structured logging migration.

CRITICAL = logging.CRITICAL
ERROR = logging.ERROR
WARNING = logging.WARNING
INFO = logging.INFO
DEBUG = logging.DEBUG


def get_request_logger(request, base_logger: logging.Logger) -> logging.Logger:
    """
    Return a logger adapter that injects request metadata (user, path, method)
    into every log record automatically.

    This is useful in view handlers where you want consistent request context
    without repeating `extra={...}` on every call.

    Usage:
        logger = get_request_logger(request, get_logger(__name__))
        logger.info("Creating ledger")  # auto-includes user, path, method
    """
    extra = {
        "user": getattr(request, "user", None),
        "path": request.path,
        "method": request.method,
    }

    class _RequestAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            kwargs.setdefault("extra", {}).update(extra)
            return msg, kwargs

    return _RequestAdapter(base_logger, extra)
