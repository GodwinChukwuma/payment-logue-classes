from __future__ import annotations
import logging
import json
from typing import Any
from datetime import datetime, timezone
import re

_SKIP = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs",
    "msg", "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "thread", "threadName", "taskName",
})

# Scrub anything that looks like a raw BVN or account number (11 digits)
_SENSITIVE_RE = re.compile(r"\b\d{11}\b")


def _scrub(value: Any) -> Any:
    if isinstance(value, str):
        return _SENSITIVE_RE.sub("[SCRUBBED]", value)
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value

class WalletJsonFormatter(logging.Formatter):
    """Single-line JSON formatter for the wallet audit log."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }

        for k, v in record.__dict__.items():
            if k not in _SKIP:
                payload[k] = v
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(_scrub(payload), default=str)
    
class WalletTransactionLogFormatter(logging.Formatter):
    
    """
    JSON formatter for two supplementary transaction log filees
    """
    _STALE_KEYS = frozenset({"event", "level", "timestamp"})

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }

        for k, v in record.__dict__.items():
            if k in _SKIP or k in self._STALE_KEYS:
                payload[k] = v
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(_scrub(payload), default=str)