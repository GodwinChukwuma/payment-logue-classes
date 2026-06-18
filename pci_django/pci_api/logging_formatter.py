from __future__ import annotations
import logging
import re
import json
from datetime import datetime, timezone
from typing import Any

# Regex catches raw PAN (13-19 consecutively)
_PAN_RE = re.compile(r"\b\d{13,19}\b")

_SKIP = frozenset({
    "args", "created", "exc_info", "exc_text", "filename", "funcName",
    "levelname", "levelno", "lineno", "message", "module", "msecs",
    "msg", "name", "pathname", "process", "processName", "relativeCreated",
    "stack_info", "thread", "threadName", "taskName",
})

def scrub(value: Any) -> Any:
    """Replace any value raw PAN lookalike with [PAN-SCRUBBED]."""
    if isinstance(value, str):
        return _PAN_RE.sub("[PAN-SCRUBBED]", value)
    if isinstance(value, dict):
        return {k: scrub(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v) for v in value]
    return value

class PCIJsonFormatter(logging.Formatter):
    """Format log as a single line JSON object"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }

        # Attach any extra field added via logger.info(extra=...)
        for key, value in record.__dict__.items():
            if key in (
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName",
            ):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        clean = scrub(payload)
        return json.dumps(clean, default=str)

class TransactionLogFormatter(logging.Formatter):
    _STALE_KEYS = ("event", "level", "timestamp")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }

        # Attach any extra field added via logger.info(extra=...)
        for k, v in record.__dict__.items():
            if k in _SKIP or k in self._STALE_KEYS:
                continue
            payload[k] = v
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(scrub(payload), default=str)
