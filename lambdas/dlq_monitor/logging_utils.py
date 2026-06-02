"""Logging estructurado JSON para dlq_monitor (consultas en CloudWatch Insights)."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

_SERVICE = "dlq_monitor"


def _build_logger() -> logging.Logger:
    logger = logging.getLogger(_SERVICE)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


_logger = _build_logger()


def log(level: str, event_type: str, correlation_id: str | None = None, **fields: Any) -> None:
    record = {
        "service": _SERVICE,
        "level": level,
        "event_type": event_type,
        "correlation_id": correlation_id,
        **fields,
    }
    _logger.log(getattr(logging, level, logging.INFO), json.dumps(record, default=str))
